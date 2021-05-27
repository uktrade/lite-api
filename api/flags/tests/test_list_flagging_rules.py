from django.urls import reverse
from rest_framework import status

from api.flags.enums import FlagStatuses
from test_helpers.clients import DataTestClient


class FlaggingRulesListTests(DataTestClient):
    url = reverse("flags:flagging_rules")

    def test_gov_user_can_see_all_flags(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_gov_user_cannot_see_flagging_rules_without_permission(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gov_user_can_see_only_filtered_case_level_flagging_rules(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        other_team = self.create_team("Team")

        flag1 = self.create_flag("Flag1", "Case", self.team)
        country_level_flag = self.create_flag("Flag2", "Organisation", self.team)
        other_team_flag = self.create_flag("Flag3", "Case", other_team)
        good_level_flag = self.create_flag("Flag4", "Case", self.team)

        flag1_rule = self.create_flagging_rule(flag=flag1, level="Case", team=self.team, matching_values=["SIEL"])
        country_level_flag_rule = self.create_flagging_rule(
            flag=country_level_flag, level="Destination", team=self.team, matching_values=["FR"]
        )
        other_team_flag_rule = self.create_flagging_rule(
            flag=other_team_flag, level="Case", team=other_team, matching_values=["OIEL"]
        )
        good_level_flag_rule = self.create_flagging_rule(
            flag=good_level_flag, level="Good", team=self.team, matching_values=["ML2a"]
        )

        url = f"{self.url}?level=Case"
        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_rules = [flagging_rule["id"] for flagging_rule in response_data["results"]]
        self.assertIn(str(flag1_rule.id), returned_rules)
        self.assertNotIn(str(country_level_flag_rule.id), returned_rules)
        self.assertIn(str(other_team_flag_rule.id), returned_rules)
        self.assertNotIn(str(good_level_flag_rule.id), returned_rules)

    def test_gov_user_can_filter_by_only_show_my_team(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        other_team = self.create_team("Team")

        country_level_flag = self.create_flag("Flag2", "Organisation", self.team)
        other_team_flag = self.create_flag("Flag3", "Case", other_team)
        country_level_flag_rule = self.create_flagging_rule(
            flag=country_level_flag, level="Destination", team=self.team, matching_values=["FR"]
        )
        other_team_flag_rule = self.create_flagging_rule(
            flag=other_team_flag, level="Case", team=other_team, matching_values=["OIEL"]
        )

        url = f"{self.url}?only_my_team=True"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_rules = [flagging_rule["id"] for flagging_rule in response_data["results"]]

        self.assertIn(str(country_level_flag_rule.id), returned_rules)
        self.assertNotIn(str(other_team_flag_rule.id), returned_rules)

    def test_gov_user_can_filter_by_active_flags(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag1 = self.create_flag("Flag1", "Case", self.team)

        flag1_rule_1 = self.create_flagging_rule(flag=flag1, level="Case", team=self.team, matching_values=["SIEL"])
        flag1_rule_2 = self.create_flagging_rule(
            flag=flag1, level="Case", team=self.team, matching_values=["OIEL"], status=FlagStatuses.DEACTIVATED
        )

        url = f"{self.url}"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_rules = [flagging_rule["id"] for flagging_rule in response_data["results"]]

        self.assertIn(str(flag1_rule_1.id), returned_rules)
        self.assertNotIn(str(flag1_rule_2.id), returned_rules)
