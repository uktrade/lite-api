from django.urls import reverse
from rest_framework import status
import uuid

from api.cases.enums import AdviceLevel, AdviceType
from api.cases.tests.factories import UserAdviceFactory, TeamAdviceFactory, FinalAdviceFactory
from api.core.helpers import date_to_drf_date
from api.users.libraries.user_to_token import user_to_token
from api.users.models import Role
from test_helpers.clients import DataTestClient
from api.staticdata.denial_reasons.models import DenialReason
from api.core import constants


class ViewCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.good = self.standard_application.goods.first().good
        self.standard_case = self.submit_application(self.standard_application)
        self.standard_case_url = reverse("cases:case", kwargs={"pk": self.standard_case.id})

    def _assert_advice(self, data, advice):
        self.assertEqual(data["id"], str(advice.id))
        self.assertEqual(data["text"], str(advice.text))
        self.assertEqual(data["note"], advice.note)
        self.assertEqual(data["type"]["key"], advice.type)
        self.assertEqual(data["level"], advice.level)
        self.assertEqual(data["proviso"], advice.proviso)
        self.assertEqual(data["denial_reasons"], list(advice.denial_reasons.values_list("id", flat=True)))
        self.assertEqual(data["footnote"], advice.footnote)
        self.assertEqual(data["user"]["first_name"], self.gov_user.first_name)
        self.assertEqual(data["user"]["last_name"], self.gov_user.last_name)
        self.assertEqual(data["user"]["team"]["name"], self.gov_user.team.name)
        self.assertEqual(data["good"], str(self.good.id))

    def test_view_all_advice(self):
        user_advice = UserAdviceFactory(user=self.gov_user, case=self.standard_case, good=self.good)
        team_advice = TeamAdviceFactory(user=self.gov_user, team=self.team, case=self.standard_case, good=self.good)
        final_advice = FinalAdviceFactory(user=self.gov_user, case=self.standard_case, good=self.good)

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["case"]["advice"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # User advice
        self.assertEqual(response_data[0]["level"], AdviceLevel.USER)
        self._assert_advice(response_data[0], user_advice)

        # Team advice
        self.assertEqual(response_data[1]["level"], AdviceLevel.TEAM)
        self._assert_advice(response_data[1], team_advice)

        # Team advice
        self.assertEqual(response_data[2]["level"], AdviceLevel.FINAL)
        self._assert_advice(response_data[2], final_advice)


class FinalAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.application)

        self.final_case_url = reverse("cases:case_final_advice", kwargs={"pk": self.case.id})

        role = Role(name="team_level")
        role.permissions.set(
            [
                constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
            ]
        )
        role.save()

        self.gov_user.role = role
        self.gov_user.save()

    def test_put_final_advice_with_refusal_note_and_nlr(self):
        refusal_uuids = {
            "7ad07d44-e5bd-45fc-92c6-6420154e0812",
            "7af31871-ac2f-4028-8b2e-97860b60a8fe",
            "79bfb05a-dc73-4727-bf54-fc5dc5ccb010",
            "133cf92e-f981-484b-8e83-fc7d615594c1",
        }

        nlr_uuids = {
            "9067a830-b639-4bff-a257-9d2c3d01ae79",
            "98cb8fed-6f3b-4f37-9ac7-9e7c9d073cd7",
            "9e3cbbd7-8a68-4512-b71e-25bfe135dcce",
            "fc50f2cc-af69-4fbe-aa78-f8518c0f9d48",
        }

        for u in nlr_uuids:
            advice = FinalAdviceFactory(
                id=uuid.UUID(u),
                user=self.gov_user,
                team=self.team,
                case=self.case,
                type=AdviceType.NO_LICENCE_REQUIRED,
            )
            advice.denial_reasons.set([DenialReason.objects.get(id="7")])

        for u in refusal_uuids:
            advice = FinalAdviceFactory(
                id=uuid.UUID(u),
                text="refusal_note_1",
                user=self.gov_user,
                team=self.team,
                case=self.case,
                type=AdviceType.REFUSE,
                is_refusal_note=True,
            )
            advice.denial_reasons.set([DenialReason.objects.get(id="7")])

        data = [
            {
                "id": "7ad07d44-e5bd-45fc-92c6-6420154e0812",
                "text": "changed_refusal_note_1",
                "denial_reasons": ["1b"],
                "footnote": None,
                "footnote_required": None,
            },
            {
                "id": "7af31871-ac2f-4028-8b2e-97860b60a8fe",
                "text": "changed_refusal_note_1",
                "denial_reasons": ["1b"],
                "footnote": None,
                "footnote_required": None,
            },
            {
                "id": "79bfb05a-dc73-4727-bf54-fc5dc5ccb010",
                "text": "changed_refusal_note_1",
                "denial_reasons": ["1b"],
                "footnote": None,
                "footnote_required": None,
            },
            {
                "id": "133cf92e-f981-484b-8e83-fc7d615594c1",
                "text": "changed_refusal_note_1",
                "denial_reasons": ["1b"],
                "footnote": None,
                "footnote_required": None,
            },
            {
                "id": "9067a830-b639-4bff-a257-9d2c3d01ae79",
                "text": "",
                "proviso": "",
                "note": "",
                "denial_reasons": [],
                "footnote": None,
                "footnote_required": None,
            },
            {
                "id": "98cb8fed-6f3b-4f37-9ac7-9e7c9d073cd7",
                "text": "",
                "proviso": "",
                "note": "",
                "denial_reasons": [],
                "footnote": None,
                "footnote_required": None,
            },
            {
                "id": "9e3cbbd7-8a68-4512-b71e-25bfe135dcce",
                "text": "",
                "proviso": "",
                "note": "",
                "denial_reasons": [],
                "footnote": None,
                "footnote_required": None,
            },
            {
                "id": "fc50f2cc-af69-4fbe-aa78-f8518c0f9d48",
                "text": "",
                "proviso": "",
                "note": "",
                "denial_reasons": [],
                "footnote": None,
                "footnote_required": None,
            },
        ]

        response = self.client.put(self.final_case_url, **self.gov_headers, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["advice"]
        matching_advice = [advice for advice in response_data if advice["id"] == data[0]["id"]][0]
        assert matching_advice["text"] == "changed_refusal_note_1"
