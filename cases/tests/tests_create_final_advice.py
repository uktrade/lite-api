from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.enums import AdviceType, AdviceLevel
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import Advice, GoodCountryDecision
from cases.tests.factories import FinalAdviceFactory, GoodCountryDecisionFactory
from api.conf import constants
from api.goods.enums import PvGrading
from api.goodstype.tests.factories import GoodsTypeFactory
from api.staticdata.countries.models import Country
from api.staticdata.decisions.models import Decision
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.teams.models import Team
from test_helpers.clients import DataTestClient
from api.users.models import GovUser, Role


class CreateCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.good = self.standard_application.goods.first().good
        self.standard_case = self.submit_application(self.standard_application)

        team_2 = Team(name="2")
        team_3 = Team(name="3")

        team_2.save()
        team_3.save()

        role = Role(name="team_level")
        role.permissions.set(
            [
                constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
                constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
                constants.GovPermissions.MANAGE_TEAM_CONFIRM_OWN_ADVICE.name,
                constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
                constants.GovPermissions.MANAGE_TEAM_ADVICE.name,
            ]
        )
        role.save()

        self.gov_user.role = role
        self.gov_user.save()

        self.gov_user_2 = GovUser(email="user@email.com", team=team_2, role=role)
        self.gov_user_3 = GovUser(email="users@email.com", team=team_3, role=role)

        self.gov_user_2.save()
        self.gov_user_3.save()

        self.standard_case_url = reverse("cases:case_final_advice", kwargs={"pk": self.standard_case.id})

    def test_advice_is_concatenated_when_final_advice_first_created(self):
        """
        Final advice is created on first call
        """
        self.create_advice(self.gov_user, self.standard_case, "end_user", AdviceType.PROVISO, AdviceLevel.TEAM)
        self.create_advice(self.gov_user_2, self.standard_case, "end_user", AdviceType.PROVISO, AdviceLevel.TEAM)
        self.create_advice(self.gov_user, self.standard_case, "good", AdviceType.NO_LICENCE_REQUIRED, AdviceLevel.TEAM)
        self.create_advice(
            self.gov_user_2, self.standard_case, "good", AdviceType.NO_LICENCE_REQUIRED, AdviceLevel.TEAM
        )

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 6)

        end_user, good = None, None
        for data in response_data:
            if data.get("end_user"):
                end_user = data.get("type").get("key")
            elif data.get("good"):
                good = data.get("type").get("key")

        self.assertEqual(end_user, AdviceType.PROVISO)
        self.assertEqual(good, AdviceType.NO_LICENCE_REQUIRED)

    def test_create_conflicting_final_advice_shows_all_fields(self):
        """
        The type should show conflicting if there are conflicting types in the advice on a single object
        """
        self.create_advice(self.gov_user, self.standard_case, "good", AdviceType.NO_LICENCE_REQUIRED, AdviceLevel.TEAM)
        self.create_advice(self.gov_user_2, self.standard_case, "good", AdviceType.REFUSE, AdviceLevel.TEAM)
        self.create_advice(self.gov_user_3, self.standard_case, "good", AdviceType.PROVISO, AdviceLevel.TEAM)

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"][0]

        self.assertEqual(response_data.get("type").get("key"), "conflicting")
        self.assertEqual(response_data.get("proviso"), "I am easy to proviso")
        self.assertCountEqual(["1a", "1b", "1c"], response_data["denial_reasons"])

    def test_create_final_advice_same_advice_type_different_pv_gradings(self):
        """
        Same advice types, different pv gradings
        """
        inputs = [
            (self.gov_user, PvGrading.UK_OFFICIAL),
            (self.gov_user_2, PvGrading.UK_OFFICIAL_SENSITIVE),
            (self.gov_user_3, PvGrading.NATO_CONFIDENTIAL),
        ]
        for user, pv_grading in inputs:
            self.create_advice(user, self.standard_case, "good", AdviceType.PROVISO, AdviceLevel.TEAM, pv_grading)

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"]

        self.assertEqual(response_data[0].get("type").get("key"), "proviso")
        self.assertEqual(response_data[0].get("proviso"), "I am easy to proviso")
        pv_gradings = Advice.objects.get(id=response_data[0]["id"]).collated_pv_grading
        self.assertIn("\n-------\n", pv_gradings)
        for _, pv_grading in inputs:
            self.assertIn(PvGrading.to_str(pv_grading), pv_gradings)

    def test_create_final_advice_same_advice_type_same_pv_gradings(self):
        """
        Same advice types, same pv gradings
        """
        pv_grading = PvGrading.OCCAR_CONFIDENTIAL
        inputs = [self.gov_user, self.gov_user_2, self.gov_user_3]
        for user in inputs:
            self.create_advice(user, self.standard_case, "good", AdviceType.PROVISO, AdviceLevel.TEAM, pv_grading)

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"]

        self.assertEqual(response_data[0].get("type").get("key"), "proviso")
        self.assertEqual(response_data[0].get("proviso"), "I am easy to proviso")
        pv_gradings = Advice.objects.get(id=response_data[0]["id"]).collated_pv_grading
        self.assertNotIn("\n-------\n", pv_gradings)
        self.assertIn(PvGrading.to_str(pv_grading), pv_gradings)

    def test_create_conflicting_final_advice_different_advice_type_same_pv_gradings(self):
        """
        Different advice types, same pv gradings
        """
        pv_grading = PvGrading.UK_OFFICIAL
        inputs = [
            (self.gov_user, AdviceType.PROVISO),
            (self.gov_user_2, AdviceType.REFUSE),
            (self.gov_user_3, AdviceType.APPROVE),
        ]
        for user, advice_type in inputs:
            self.create_advice(user, self.standard_case, "good", advice_type, AdviceLevel.TEAM, pv_grading)

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"]

        self.assertEqual(response_data[0].get("type").get("key"), "conflicting")
        pv_gradings = Advice.objects.get(id=response_data[0]["id"]).collated_pv_grading
        self.assertNotIn("\n-------\n", pv_gradings)
        self.assertIn(PvGrading.to_str(pv_grading), pv_gradings)

    def test_create_conflicting_final_advice_different_advice_type_different_pv_gradings(self):
        """
        Different advice types, different pv gradings
        """
        inputs = [
            (self.gov_user, AdviceType.PROVISO, PvGrading.UK_OFFICIAL),
            (self.gov_user_2, AdviceType.REFUSE, PvGrading.UK_OFFICIAL_SENSITIVE),
            (self.gov_user_3, AdviceType.APPROVE, PvGrading.NATO_CONFIDENTIAL),
        ]
        for user, advice_type, pv_grading in inputs:
            self.create_advice(user, self.standard_case, "good", advice_type, AdviceLevel.TEAM, pv_grading)

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"]

        self.assertEqual(response_data[0].get("type").get("key"), "conflicting")
        pv_gradings = Advice.objects.get(id=response_data[0]["id"]).collated_pv_grading
        self.assertIn("\n-------\n", pv_gradings)
        for _, _, pv_grading in inputs:
            self.assertIn(PvGrading.to_str(pv_grading), pv_gradings)

    # Normal restrictions on team advice items
    @parameterized.expand(
        [
            [AdviceType.APPROVE],
            [AdviceType.PROVISO],
            [AdviceType.REFUSE],
            [AdviceType.NO_LICENCE_REQUIRED],
            [AdviceType.NOT_APPLICABLE],
        ]
    )
    def test_create_end_user_case_final_advice(self, advice_type):
        """
        Tests that a gov user can create an approval/proviso/refuse/nlr/not_applicable
        piece of team level advice for an end user
        """
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": advice_type,
            "end_user": str(self.standard_application.end_user.party.id),
        }

        if advice_type == AdviceType.PROVISO:
            data["proviso"] = "I am easy to proviso"

        if advice_type == AdviceType.REFUSE:
            data["denial_reasons"] = ["1a", "1b", "1c"]

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Advice.objects.get())

    def test_user_cannot_create_final_advice_without_permissions(self):
        """
        Tests that the permissions are required to perform final level actions
        """
        self.gov_user.role.permissions.set([])
        self.gov_user.save()
        response = self.client.get(self.standard_case_url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.standard_case_url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete(self.standard_case_url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_submit_user_level_advice_if_final_advice_exists_on_that_case(self):
        """
        Logically blocks the submission of lower tier advice if higher tier advice exists
        """
        FinalAdviceFactory(user=self.gov_user_2, case=self.standard_case, good=self.good)

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.standard_application.end_user.party.id),
        }

        response = self.client.post(
            reverse("cases:user_advice", kwargs={"pk": self.standard_case.id}), **self.gov_headers, data=[data]
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_submit_user_level_advice_if_final_advice_has_been_cleared_for_that_team_on_that_case(self,):
        """
        No residual data is left to block lower tier advice being submitted after a clear
        """
        self.create_advice(self.gov_user_2, self.standard_case, "good", AdviceType.PROVISO, AdviceLevel.USER)

        self.client.delete(self.standard_case_url, **self.gov_headers)

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.standard_application.end_user.party.id),
        }

        response = self.client.post(
            reverse("cases:user_advice", kwargs={"pk": self.standard_case.id}), **self.gov_headers, data=[data]
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_submit_team_level_advice_if_final_advice_exists_for_that_team_on_that_case(self,):
        """
        Logically blocks the submission of lower tier advice if higher tier advice exists
        """
        self.create_advice(self.gov_user_2, self.standard_case, "good", AdviceType.PROVISO, AdviceLevel.FINAL)

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.standard_application.end_user.party.id),
        }

        response = self.client.post(
            reverse("cases:team_advice", kwargs={"pk": self.standard_case.id}), **self.gov_headers, data=[data]
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_submit_team_level_advice_if_final_advice_has_been_cleared_for_that_team_on_that_case(self,):
        """
        No residual data is left to block lower tier advice being submitted after a clear
        """
        self.create_advice(self.gov_user_2, self.standard_case, "good", AdviceType.PROVISO, AdviceLevel.TEAM)

        self.client.delete(self.standard_case_url, **self.gov_headers)

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.standard_application.end_user.party.id),
        }

        response = self.client.post(
            reverse("cases:team_advice", kwargs={"pk": self.standard_case.id}), **self.gov_headers, data=[data]
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_and_delete_audit_trail_is_created_when_the_appropriate_actions_take_place(self,):
        """
        Audit trail is created when clearing or combining advice
        """
        self.create_advice(
            self.gov_user, self.standard_case, "end_user", AdviceType.NO_LICENCE_REQUIRED, AdviceLevel.TEAM
        )
        self.create_advice(self.gov_user_2, self.standard_case, "good", AdviceType.REFUSE, AdviceLevel.TEAM)
        self.create_advice(self.gov_user_3, self.standard_case, "good", AdviceType.PROVISO, AdviceLevel.TEAM)

        self.client.get(self.standard_case_url, **self.gov_headers)
        self.client.delete(self.standard_case_url, **self.gov_headers)

        response = self.client.get(reverse("cases:activity", kwargs={"pk": self.standard_case.id}), **self.gov_headers)

        self.assertEqual(len(response.json()["activity"]), 3)

    def test_creating_final_advice_does_not_overwrite_user_level_advice_or_team_level_advice(self,):
        """
        Because of the shared parent class, make sure the parent class "save" method is overridden by the child class
        """
        self.create_advice(
            self.gov_user, self.standard_case, "end_user", AdviceType.NO_LICENCE_REQUIRED, AdviceLevel.USER
        )
        self.create_advice(
            self.gov_user, self.standard_case, "end_user", AdviceType.NO_LICENCE_REQUIRED, AdviceLevel.TEAM
        )
        self.create_advice(
            self.gov_user, self.standard_case, "end_user", AdviceType.NO_LICENCE_REQUIRED, AdviceLevel.FINAL
        )

        self.client.get(self.standard_case_url, **self.gov_headers)

        self.assertEqual(Advice.objects.count(), 3)

    @parameterized.expand(CaseStatusEnum.terminal_statuses())
    def test_cannot_create_final_advice_on_case_in_terminal_state(self, terminal_status):
        self.standard_application.status = get_case_status_by_status(terminal_status)
        self.standard_application.save()

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.standard_application.end_user.party.id),
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_entity_from_final_advice_model(self):
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.standard_application.end_user.party.id),
        }

        self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        advice_object = Advice.objects.get(entity_id=self.standard_application.end_user.party.id)
        self.assertEqual(str(advice_object.end_user.id), data["end_user"])
        self.assertEqual(advice_object.entity, advice_object.end_user)

        entity_field = Advice.ENTITY_FIELDS.copy()
        entity_field.remove("end_user")
        for field in entity_field:
            self.assertIsNone(getattr(advice_object, field, None))

    def test_updating_final_advice_removes_draft_decision_documents(self):
        good = self.standard_application.goods.first().good
        FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=self.standard_case, good=good, type=AdviceType.APPROVE,
        )
        template = self.create_letter_template(
            case_types=[self.standard_case.case_type], decisions=[Decision.objects.get(name=AdviceType.APPROVE)],
        )
        self.create_generated_case_document(
            self.standard_case, template, advice_type=AdviceType.APPROVE, visible_to_exporter=False
        )

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "good": str(good.id),
        }
        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(GeneratedCaseDocument.objects.filter(case=self.standard_case).exists())


class CreateFinalAdviceOpenApplicationTests(DataTestClient):
    def test_change_approve_final_advice_deletes_good_country_decisions(self):
        self.gov_user.role.permissions.set(
            [constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,]
        )
        case = self.create_open_application_case(self.organisation)
        url = reverse("cases:case_final_advice", kwargs={"pk": case.id})
        goods_type = GoodsTypeFactory(application=case)
        FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=case, goods_type=goods_type, type=AdviceType.APPROVE,
        )
        GoodCountryDecisionFactory(case=case, goods_type=goods_type, country=Country.objects.first())

        data = {
            "text": "Changed my mind. Reject this",
            "type": AdviceType.REFUSE,
            "goods_type": str(goods_type.id),
        }
        response = self.client.post(url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["advice"][0]["goods_type"], str(goods_type.id))
        self.assertFalse(GoodCountryDecision.objects.filter(goods_type=goods_type).exists())
