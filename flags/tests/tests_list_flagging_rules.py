from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class FlagsListTests(DataTestClient):
    url = reverse("flags:flagging_rules")

    def test_gov_user_can_see_all_flags(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_gov_user_can_see_only_filtered_case_level_and_team_flags(self):
        other_team = self.create_team("Team")

        flag1 = self.create_flag("Flag1", "Case", self.team)
        country_level_flag = self.create_flag("Flag2", "Organisation", self.team)
        other_team_flag = self.create_flag("Flag3", "Case", other_team)
        good_level_flag = self.create_flag("Flag4", "Case", self.team)

        flag1_rule = self.create_flagging_rule(flag=flag1, level="Case", team=self.team, matching_value="SIEL")
        country_level_flag_rule = self.create_flagging_rule(
            flag=country_level_flag, level="Destination", team=self.team, matching_value="FR"
        )
        other_team_flag_rule = self.create_flagging_rule(
            flag=other_team_flag, level="Case", team=other_team, matching_value="OIEL"
        )
        good_level_flag_rule = self.create_flagging_rule(
            flag=good_level_flag, level="Good", team=good_level_flag, matching_value="ML2a"
        )

        url = f"{self.url}?level=Case&team={self.team.name}&include_deactivated=False"
        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_rules = [flagging_rule["id"] for flagging_rule in response_data["results"]]
        self.assertIn(str(flag1_rule.id), returned_rules)
        self.assertNotIn(str(country_level_flag_rule.id), returned_rules)
        self.assertNotIn(str(other_team_flag_rule.id), returned_rules)
        self.assertIn(str(good_level_flag_rule.id), returned_rules)
