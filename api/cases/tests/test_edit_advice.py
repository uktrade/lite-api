from copy import deepcopy
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.applications.models import StandardApplication
from api.cases.enums import AdviceType, AdviceLevel
from api.cases.models import Advice, Case
from api.core.constants import GovPermissions
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.users.models import Role

from test_helpers.clients import DataTestClient


class EditCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.case)
        self.application = StandardApplication.objects.get(id=self.case.id)
        self.url = reverse("cases:user_advice", kwargs={"pk": self.case.id})

    def test_edit_standard_case_advice_twice_only_shows_once(self):
        """
        Tests that a gov user cannot create two pieces of advice on the same
        case item (be that a good or destination)
        """
        data = {
            "type": AdviceType.APPROVE,
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "country": "GB",
            "level": AdviceLevel.USER,
        }

        self.client.post(self.url, **self.gov_headers, data=[data])
        self.client.post(self.url, **self.gov_headers, data=[data])

        # Assert that there's only one piece of advice
        self.assertEqual(Advice.objects.count(), 1)


class AdviceFinalLevelUpdateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_draft_standard_application(self.organisation)
        self.submit_application(self.case)
        self.application = StandardApplication.objects.get(id=self.case.id)
        self.url = reverse("cases:case_final_advice", kwargs={"pk": self.case.id})
        permissions = [
            GovPermissions.MANAGE_LICENCE_FINAL_ADVICE,
            GovPermissions.MANAGE_LICENCE_DURATION,
        ]
        self.gov_user.role = Role.objects.create(name="Final Advice test")
        self.gov_user.role.permissions.set([permission.name for permission in permissions])
        self.gov_user.save()

        self._setup_advice_for_application(self.application, AdviceType.APPROVE, AdviceLevel.FINAL)
        self.advice_qs = Advice.objects.filter(case=self.case, level=AdviceLevel.FINAL, type=AdviceType.APPROVE)

    def _setup_advice_for_application(self, application, advice_type, advice_level):
        # Create Advice objects for all entities
        for good_on_application in application.goods.all():
            self.create_advice(
                self.gov_user,
                application,
                "",
                advice_type,
                advice_level,
                good=good_on_application.good,
            )
        for party_on_application in application.parties.all():
            self.create_advice(
                self.gov_user,
                application,
                party_on_application.party.type,
                advice_type,
                advice_level,
            )

    @parameterized.expand(CaseStatusEnum._terminal_statuses)
    def test_advice_cannot_be_edited_for_terminal_cases(self, case_status):
        self.case.status = CaseStatus.objects.get(status=case_status)
        self.case.save()

        data = [
            {
                "id": advice.id,
                "text": "updating previous recommendation with more details",
                "note": "No additional instructions",
            }
            for advice in self.advice_qs
        ]
        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            ["You can only perform this operation on a case in a non-terminal state"],
        )

    @parameterized.expand(
        [
            AdviceLevel.USER,
            AdviceLevel.TEAM,
        ]
    )
    def test_edit_advice_level_returns_error(self, level):
        data = [
            {
                "id": advice.id,
                "text": "updating previous recommendation with more details",
                "note": "No additional instructions",
                "level": level,
            }
            for advice in self.advice_qs
        ]
        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            ["Advice level cannot be updated once it is created"],
        )

    @parameterized.expand(
        [
            AdviceLevel.USER,
            AdviceLevel.TEAM,
        ]
    )
    def test_edit_advice_invalid_data_returns_error(self, level):
        data = [
            {
                "id": advice.id,
                "type": "invalid",
                "text": "updating previous recommendation with more details",
                "note": "No additional instructions",
            }
            for advice in self.advice_qs
        ]
        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            [
                {"type": ['"invalid" is not a valid choice.']},
                {"type": ['"invalid" is not a valid choice.']},
                {"type": ['"invalid" is not a valid choice.']},
                {"type": ['"invalid" is not a valid choice.']},
            ],
        )

    @parameterized.expand(
        [
            (
                AdviceType.APPROVE,
                {
                    "text": "updating previous recommendation with more details",
                    "proviso": "",
                    "note": "no additional instructions",
                    "denial_reasons": [],
                },
            ),
            (
                AdviceType.PROVISO,
                {
                    "text": "updating previous recommendation with more details",
                    "proviso": "Updated licence conditions",
                    "note": "with further instructions",
                    "denial_reasons": [],
                },
            ),
            (
                AdviceType.REFUSE,
                {
                    "text": "Recommending refuse",
                    "proviso": "",
                    "note": "",
                    "denial_reasons": ["1", "1d", "2", "4"],
                },
            ),
            (
                AdviceType.NO_LICENCE_REQUIRED,
                {
                    "text": "",
                    "proviso": "",
                    "note": "",
                    "denial_reasons": [],
                },
            ),
        ]
    )
    def test_edit_final_level_advice_types_success(self, advice_type, advice_data):
        Advice.objects.all().delete()

        self._setup_advice_for_application(self.application, advice_type, AdviceLevel.FINAL)
        advice_qs = Advice.objects.filter(case=self.case, level=AdviceLevel.FINAL, type=advice_type)
        advice_ids = advice_qs.values_list("id", flat=True)

        data = []
        for advice in advice_qs:
            entity_data = deepcopy(advice_data)
            entity_data["id"] = advice.id
            data.append(entity_data)

        response = self.client.put(self.url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["advice"]
        for index, advice in enumerate(list(advice_qs)):
            advice.refresh_from_db()

            self.assertEqual(response[index]["text"], data[index]["text"])
            self.assertEqual(response[index]["proviso"], data[index]["proviso"])
            self.assertEqual(response[index]["note"], data[index]["note"])
            self.assertEqual(response[index]["denial_reasons"], data[index]["denial_reasons"])

            self.assertEqual(advice.text, data[index]["text"])
            self.assertEqual(advice.proviso, data[index]["proviso"])
            self.assertEqual(advice.note, data[index]["note"])
            self.assertEqual([d.id for d in advice.denial_reasons.all()], data[index]["denial_reasons"])

        ids_after_update = Advice.objects.filter(case=self.case, level=AdviceLevel.FINAL, type=advice_type).values_list(
            "id", flat=True
        )
        self.assertEqual(sorted(advice_ids), sorted(ids_after_update))
