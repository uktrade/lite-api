import pytest

from django.test import override_settings
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status
from uuid import uuid4

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.cases.enums import AdviceType, CountersignOrder
from api.cases.models import Advice, CountersignAdvice
from api.cases.tests.factories import CountersignAdviceFactory
from api.core.constants import GovPermissions, Roles
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.teams.enums import TeamIdEnum
from api.teams.models import Department, Team
from api.users.models import GovUser, Role
from test_helpers.clients import DataTestClient


class CreateCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.application)

        self.standard_case_url = reverse("cases:user_advice", kwargs={"pk": self.case.id})
        self.final_case_url = reverse("cases:case_final_advice", kwargs={"pk": self.case.id})

    def test_create_advice_good(self):
        data = {
            "user": self.gov_user.baseuser_ptr.id,
            "good": str(self.application.goods.first().good.id),
            "text": "Text",
            "type": AdviceType.APPROVE,
            "level": "user",
            "team": self.team.id,
            "proviso": "",
            "denial_reasons": [],
            "note": "",
            "footnote": None,
            "footnote_required": "False",
            "case": self.case.id,
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Advice.objects.get())
        self.assertTrue(Audit.objects.filter(verb=AuditType.CREATED_USER_ADVICE).exists())

    def test_create_advice_good_on_application(self):
        data = {
            "user": self.gov_user.baseuser_ptr.id,
            "good": str(self.application.goods.first().id),
            "text": "Text",
            "type": AdviceType.APPROVE,
            "level": "user",
            "team": self.team.id,
            "proviso": "",
            "denial_reasons": [],
            "note": "",
            "footnote": None,
            "footnote_required": "False",
            "case": self.case.id,
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Advice.objects.get())
        self.assertTrue(Audit.objects.filter(verb=AuditType.CREATED_USER_ADVICE).exists())

    @parameterized.expand(
        [
            AdviceType.APPROVE,
            AdviceType.PROVISO,
            AdviceType.REFUSE,
            AdviceType.NO_LICENCE_REQUIRED,
            AdviceType.NOT_APPLICABLE,
        ]
    )
    def test_create_end_user_case_advice(self, advice_type):
        """
        Tests that a gov user can create an approval/proviso/refuse/nlr/not_applicable
        piece of advice for an end user
        """
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": advice_type,
            "end_user": str(self.application.end_user.party.id),
        }

        if advice_type == AdviceType.PROVISO:
            data["proviso"] = "I am easy to proviso"

        if advice_type == AdviceType.REFUSE:
            data["denial_reasons"] = ["1a", "1b", "1c"]

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Advice.objects.get())
        self.assertTrue(Audit.objects.filter(verb=AuditType.CREATED_USER_ADVICE).exists())

    @pytest.mark.xfail(reason="This test was set up incorrectly so never worked as intended")
    def test_cannot_create_advice_for_two_items(self):
        """
        Tests that a gov user cannot create a piece of advice for more than one item
        """
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            # this passes the GoodOnApplication id to the Advice model which is why we get a 400 here
            # NOT because the user is trying to create advice for two different items
            "good": str(self.application.goods.first().id),
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Advice.objects.count(), 0)

    @parameterized.expand(CaseStatusEnum.terminal_statuses())
    def test_cannot_create_advice_when_case_in_terminal_state(self, terminal_status):
        self.application.status = get_case_status_by_status(terminal_status)
        self.application.save()

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "good": str(self.application.goods.first().id),
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_add_footnote_without_permission(self):
        self.gov_user.role.permissions.remove(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "footnote_required": "True",
            "footnote": "footnote",
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        response_data = response.json()["advice"][0]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["footnote"], None)
        self.assertEqual(Advice.objects.filter(footnote_required=None, footnote=None).count(), 1)

    def test_cannot_create_advice_without_footnote_and_having_permission(self):
        self.gov_user.role.permissions.add(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_create_advice_with_footnote_not_required(self):
        self.gov_user.role.permissions.add(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "footnote_required": "False",
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        response_data = response.json()["advice"][0]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["footnote"], None)
        self.assertEqual(Advice.objects.filter(footnote_required=False, footnote=None).count(), 1)

    def test_cannot_create_advice_with_footnote_required_and_no_footnote(self):
        self.gov_user.role.permissions.add(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "footnote_required": "True",
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_create_advice_with_footnote_required(self):
        self.gov_user.role.permissions.add(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "footnote_required": "True",
            "footnote": "footnote",
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        response_data = response.json()["advice"][0]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["footnote"], "footnote")
        self.assertEqual(Advice.objects.filter(footnote_required=True, footnote=data["footnote"]).count(), 1)

    @parameterized.expand(
        [
            [AdviceType.APPROVE, " added a recommendation to approve."],
            [AdviceType.REFUSE, " added a recommendation to refuse."],
            [AdviceType.PROVISO, " added a licence condition."],
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_create_lu_final_advice_has_audit(self, advice_type, expected_text):
        lu_team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        lu_user = GovUser(baseuser_ptr=self.base_user, team=lu_team)
        super_user_role = Role.objects.get(id=Roles.INTERNAL_SUPER_USER_ROLE_ID)
        lu_user.role = super_user_role
        lu_user.save()
        data = {
            "user": lu_user.baseuser_ptr.id,
            "good": str(self.application.goods.first().good.id),
            "text": "Text",
            "type": advice_type,
            "level": "final",
            "team": self.team.id,
            "proviso": "Proviso text" if advice_type == AdviceType.PROVISO else "",
            "denial_reasons": [] if advice_type == AdviceType.APPROVE else ["WMD"],
            "note": "",
            "footnote": None,
            "footnote_required": "False",
            "case": self.case.id,
        }

        response = self.client.post(self.final_case_url, **self.gov_headers, data=[data])

        assert response.status_code == status.HTTP_201_CREATED

        lu_advice_audit = Audit.objects.filter(verb=AuditType.LU_ADVICE)

        assert lu_advice_audit.exists()
        audit_obj = lu_advice_audit.first()
        audit_text = AuditSerializer(audit_obj).data["text"]
        assert audit_text == expected_text
        assert audit_obj.payload["firstname"] == "John"  # /PS-IGNORE
        assert audit_obj.payload["lastname"] == "Smith"  # /PS-IGNORE
        assert audit_obj.payload["advice_type"] == advice_type
        if advice_type == AdviceType.PROVISO:
            assert audit_obj.payload.get("additional_text") == data["proviso"]
        else:
            assert audit_obj.payload.get("additional_text") is None

    @parameterized.expand(
        [
            [AdviceType.APPROVE, " edited their approval reason."],
            [AdviceType.REFUSE, " edited their refusal reason."],
            [AdviceType.PROVISO, " edited a licence condition."],
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_update_lu_final_advice_has_audit(self, advice_type, expected_text):
        lu_team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        lu_user = GovUser(baseuser_ptr=self.base_user, team=lu_team)
        super_user_role = Role.objects.get(id=Roles.INTERNAL_SUPER_USER_ROLE_ID)
        lu_user.role = super_user_role
        lu_user.save()

        data = {
            "user": lu_user.baseuser_ptr.id,
            "good": str(self.application.goods.first().good.id),
            "text": "Text",
            "type": advice_type,
            "level": "final",
            "team": self.team.id,
            "proviso": "Proviso text" if advice_type == AdviceType.PROVISO else "",
            "denial_reasons": [] if advice_type == AdviceType.APPROVE else ["WMD"],
            "note": "",
            "footnote": None,
            "footnote_required": "False",
            "case": self.case.id,
        }

        # Add initial advice to DB:
        resp = self.client.post(self.final_case_url, **self.gov_headers, data=[data])
        data["text"] = "Updated Text"
        if advice_type == AdviceType.PROVISO:
            data["proviso"] = "Edited Proviso text"
        data["id"] = resp.json()["advice"][0]["id"]

        # Update advice
        response = self.client.put(self.final_case_url, **self.gov_headers, data=[data])

        assert response.status_code == status.HTTP_200_OK

        lu_advice_audit = Audit.objects.filter(verb=AuditType.LU_EDIT_ADVICE)
        assert lu_advice_audit.exists()
        audit_obj = lu_advice_audit.first()
        audit_text = AuditSerializer(audit_obj).data["text"]
        assert audit_text == expected_text
        assert audit_obj.payload["firstname"] == "John"  # /PS-IGNORE
        assert audit_obj.payload["lastname"] == "Smith"  # /PS-IGNORE
        assert audit_obj.payload["advice_type"] == advice_type
        if advice_type == AdviceType.PROVISO:
            assert audit_obj.payload.get("additional_text") == "Edited Proviso text"
        else:
            assert audit_obj.payload["additional_text"] == "Updated Text"

    @parameterized.expand(
        [
            (AdviceType.CONFLICTING,),
            (AdviceType.NOT_APPLICABLE,),
            (AdviceType.NO_LICENCE_REQUIRED,),
            (AdviceType.CONFLICTING,),
            (AdviceType.NOT_APPLICABLE,),
            (AdviceType.NO_LICENCE_REQUIRED,),
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_advice_has_no_audit_for_unsupported_advice_types(self, advice_type):
        lu_team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        lu_user = GovUser(baseuser_ptr=self.base_user, team=lu_team)
        super_user_role = Role.objects.get(id=Roles.INTERNAL_SUPER_USER_ROLE_ID)
        lu_user.role = super_user_role
        lu_user.save()

        data = {
            "user": lu_user.baseuser_ptr.id,
            "good": str(self.application.goods.first().good.id),
            "text": "Text",
            "type": advice_type,
            "level": "final",
            "team": self.team.id,
            "proviso": "Provided you buy me an ice-cream",
            "denial_reasons": [] if advice_type == AdviceType.APPROVE else ["WMD"],
            "note": "",
            "footnote": None,
            "footnote_required": "False",
            "case": self.case.id,
        }

        # Add initial advice to DB:
        resp = self.client.post(self.final_case_url, **self.gov_headers, data=[data])
        data["id"] = resp.json()["advice"][0]["id"]

        # Update advice
        response = self.client.put(self.final_case_url, **self.gov_headers, data=[data])

        assert response.status_code == status.HTTP_200_OK

        lu_advice_audit = Audit.objects.filter(verb=AuditType.LU_ADVICE)
        lu_advice_update_audit = Audit.objects.filter(verb=AuditType.LU_EDIT_ADVICE)
        assert not lu_advice_audit.exists()
        assert not lu_advice_update_audit.exists()


class CountersignAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.application)

        self.url = reverse("cases:countersign_advice", kwargs={"pk": self.case.id})

    def test_countersign_advice_terminal_status_failure(self):
        """Ensure we cannot countersign a case that is in one of the terminal state"""
        case_url = reverse("cases:case", kwargs={"pk": self.case.id})
        data = {"status": CaseStatusEnum.WITHDRAWN, "note": "test"}
        response = self.client.patch(case_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(self.url, **self.gov_headers, data=[])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_countersign_advice_success(self):
        """Ensure we can countersign a case with advice given by multiple users and it
        emits an audit log"""
        all_advice = [
            Advice.objects.create(
                **{
                    "user": self.gov_user,
                    "good": self.application.goods.first().good,
                    "team": self.team,
                    "case": self.case,
                    "note": f"Advice {i}",
                }
            )
            for i in range(4)
        ]

        data = [
            {
                "id": advice.id,
                "countersigned_by": self.gov_user.baseuser_ptr.id,
                "comments": "Agree with recommendation",
            }
            for advice in all_advice
        ]

        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        audit_qs = Audit.objects.filter(verb=AuditType.COUNTERSIGN_ADVICE)
        self.assertEqual(audit_qs.count(), 1)
        self.assertEqual(audit_qs.first().actor, self.gov_user)


class CountersignAdviceWithDecisionTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.application)

        self.url = reverse("cases:countersign_decision_advice", kwargs={"pk": self.case.id})

    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=False)
    def test_countersign_advice_without_routing_enabled_fails(self):
        data = [
            {
                "order": CountersignOrder.FIRST_COUNTERSIGN,
                "outcome_accepted": True,
                "reasons": "Agree with the original outcome",
                "countersigned_user": self.gov_user.baseuser_ptr.id,
                "advice": "1234",
            }
        ]
        response = self.client.post(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_countersign_advice_with_decision_terminal_status_failure(self):
        """Ensure we cannot countersign a case that is in one of the terminal state"""
        case_url = reverse("cases:case", kwargs={"pk": self.case.id})
        data = {"status": CaseStatusEnum.WITHDRAWN, "note": "test"}
        response = self.client.patch(case_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.url, **self.gov_headers, data=[])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.put(self.url, **self.gov_headers, data=[])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_countersign_advice_with_decision_serializer_invalid_failure(self):
        data = [
            {
                "order": CountersignOrder.FIRST_COUNTERSIGN,
                "reasons": "Agree with the original outcome",
                "countersigned_user": self.gov_user.baseuser_ptr.id,
                "advice": str(uuid4()),
            }
        ]

        response = self.client.post(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data[0]["id"] = str(uuid4())

        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            [
                "DIT",
                CountersignOrder.FIRST_COUNTERSIGN,
                True,
                "Accepted reason",
                " countersigned all DIT recommendations.",
            ],
            [
                None,
                CountersignOrder.FIRST_COUNTERSIGN,
                False,
                "Refused reason",
                " declined to countersign department recommendations.",
            ],
            [
                None,
                CountersignOrder.SECOND_COUNTERSIGN,
                True,
                "Senior accepted reason",
                " senior countersigned all department recommendations.",
            ],
            [
                "MOD",
                CountersignOrder.SECOND_COUNTERSIGN,
                False,
                "Senior refused reason",
                " declined to senior countersign MOD recommendations.",
            ],
        ]
    )
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_countersign_advice_with_decision_success(self, dept, order, outcome_accepted, reason, expected_text):
        if dept:
            self.gov_user.team.department = Department.objects.get(name=dept)
            self.gov_user.team.save()

        all_advice = [
            Advice.objects.create(
                **{
                    "user": self.gov_user,
                    "good": self.application.goods.first().good,
                    "team": self.team,
                    "case": self.case,
                    "note": f"Advice {i}",
                }
            )
            for i in range(4)
        ]

        data = [
            {
                "order": order,
                "outcome_accepted": outcome_accepted,
                "reasons": reason,
                "countersigned_user": self.gov_user.baseuser_ptr.id,
                "case": self.case.id,
                "advice": advice.id,
            }
            for advice in all_advice
        ]

        response = self.client.post(self.url, **self.gov_headers, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert CountersignAdvice.objects.count() == len(data)
        audit_qs = Audit.objects.filter(verb=AuditType.LU_COUNTERSIGN)
        assert audit_qs.count() == 1
        audit = audit_qs.first()
        audit_text = AuditSerializer(audit).data["text"]
        assert audit.actor == self.gov_user
        assert audit_text == expected_text
        payload = audit.payload
        if not outcome_accepted:
            assert payload["additional_text"] == reason
        else:
            assert "additional_text" not in payload

    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    def test_countersign_advice_with_decision_update_success(self):
        all_advice = [
            Advice.objects.create(
                **{
                    "user": self.gov_user,
                    "good": self.application.goods.first().good,
                    "team": self.team,
                    "case": self.case,
                    "note": f"Advice {i}",
                }
            )
            for i in range(2)
        ]

        # create few instances of countersigned advice
        countersign_advice = [CountersignAdviceFactory(case=self.case, advice=advice) for advice in all_advice]

        data = [
            {
                "id": countersign_advice[0].id,
                "outcome_accepted": False,
                "reasons": "Agree with the original outcome",
                "countersigned_user": self.gov_user.baseuser_ptr.id,
            },
            {
                "id": countersign_advice[1].id,
                "outcome_accepted": True,
                "reasons": "Disagree with the original outcome",
                "countersigned_user": self.gov_user.baseuser_ptr.id,
            },
        ]

        # edit countersigned advice
        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        for index, item in enumerate(response["countersign_advice"]):
            self.assertEqual(item["outcome_accepted"], data[index]["outcome_accepted"])
            self.assertEqual(item["reasons"], data[index]["reasons"])

            obj = countersign_advice[index]
            obj.refresh_from_db()
            self.assertEqual(item["outcome_accepted"], obj.outcome_accepted)
            self.assertEqual(item["reasons"], obj.reasons)

        audit_qs = Audit.objects.filter(verb=AuditType.COUNTERSIGN_ADVICE)
        self.assertEqual(audit_qs.count(), 1)
        self.assertEqual(audit_qs.first().actor, self.gov_user)
