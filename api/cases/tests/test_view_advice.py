from django.urls import reverse
from rest_framework import status

from api.cases.enums import AdviceLevel
from api.cases.tests.factories import UserAdviceFactory, TeamAdviceFactory, FinalAdviceFactory
from api.core.helpers import date_to_drf_date
from test_helpers.clients import DataTestClient


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
