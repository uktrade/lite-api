from django.urls import reverse
from rest_framework import status

from cases.enums import AdviceLevel
from cases.tests.factories import UserAdviceFactory, TeamAdviceFactory, FinalAdviceFactory
from conf.helpers import date_to_drf_date
from test_helpers.clients import DataTestClient
from test_helpers.helpers import node_by_id


class ViewCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.good = self.standard_application.goods.first().good
        self.standard_case = self.submit_application(self.standard_application)
        self.standard_case_url = reverse("cases:case", kwargs={"pk": self.standard_case.id})

    def test_view_all_advice(self):
        user_advice = UserAdviceFactory(user=self.gov_user, case=self.standard_case, good=self.good)
        team_advice = TeamAdviceFactory(user=self.gov_user, team=self.team, case=self.standard_case, good=self.good)
        final_advice = FinalAdviceFactory(user=self.gov_user, case=self.standard_case, good=self.good)

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["case"]["advice"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for advice in [user_advice, team_advice, final_advice]:
            comparison_dict = {
                    "id": str(advice.id),
                    "text": advice.text,
                    "note": advice.note,
                    "level": advice.level,
                    "case": str(advice.case.id),
                    "type": {"key": advice.type, "value": "Approve"},
                    "updated_at": date_to_drf_date(advice.updated_at),
                    "created_at": date_to_drf_date(advice.created_at),
                    "good": str(self.good.id),
                    "user": {
                        "email": self.gov_user.email,
                        "first_name": self.gov_user.first_name,
                        "last_name": self.gov_user.last_name,
                        "id": str(self.gov_user.id),
                        "status": "Active",
                    }
                }

            if advice.level == AdviceLevel.TEAM:
                comparison_dict["team"] = {"id": str(self.team.id), "name": self.team.name}

            self.assertEqual(node_by_id(response_data, advice.id), comparison_dict)
