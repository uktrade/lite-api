from django.urls import reverse
from rest_framework import status

from api.flags.enums import FlagStatuses, FlagLevels
from api.flags.tests.factories import FlagFactory
from test_helpers.clients import DataTestClient


class FlaggingRulesUpdateTest(DataTestClient):
    def test_flagging_rule_can_be_deactivated(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = self.create_flag("New Flag", "Case", self.team)
        flagging_rule = self.create_flagging_rule(level="Case", flag=flag, team=self.team, matching_values=["SIEL"])

        data = {
            "status": FlagStatuses.DEACTIVATED,
        }

        url = reverse("flags:flagging_rule", kwargs={"pk": flagging_rule.id})
        response = self.client.put(url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["flagging_rule"]["status"], FlagStatuses.DEACTIVATED)

    def test_flagging_rule_cannot_be_deactivated_by_a_user_outside_flags_team(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        team = self.create_team("Secondary team")
        flag = self.create_flag("New Flag", "Case", team)
        flagging_rule = self.create_flagging_rule(level="Case", flag=flag, team=team, matching_values=["SIEL"])

        data = {
            "status": FlagStatuses.DEACTIVATED,
        }

        url = reverse("flags:flagging_rule", kwargs={"pk": flagging_rule.id})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(flag.status, FlagStatuses.ACTIVE)

    def test_flagging_rule_level_cannot_be_changed(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("New Flag", "Case", self.team)
        flagging_rule = self.create_flagging_rule(level="Case", flag=flag, team=self.team, matching_values=["SIEL"])

        data = {
            "level": "Good",
        }

        url = reverse("flags:flagging_rule", kwargs={"pk": flagging_rule.id})
        self.client.put(url, data, **self.gov_headers)

        self.assertEqual(flagging_rule.level, "Case")

    def test_flagging_rule_can_change_flag(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("New Flag", "Case", self.team)
        flag_2 = self.create_flag("other flag", "Case", self.team)
        flagging_rule = self.create_flagging_rule(level="Case", flag=flag, team=self.team, matching_values=["SIEL"])

        data = {
            "flag": str(flag_2.id),
        }

        url = reverse("flags:flagging_rule", kwargs={"pk": flagging_rule.id})
        self.client.put(url, data, **self.gov_headers)

        flagging_rule.refresh_from_db()

        self.assertEqual(flagging_rule.flag, flag_2)

    def test_flagging_rule_can_change_matching_values(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("New Flag", "Case", self.team)
        flagging_rule = self.create_flagging_rule(level="Case", flag=flag, team=self.team, matching_values=["SIEL"])

        data = {
            "matching_values": ["OIEL"],
        }

        url = reverse("flags:flagging_rule", kwargs={"pk": flagging_rule.id})
        self.client.put(url, data, **self.gov_headers)

        flagging_rule.refresh_from_db()

        self.assertEqual(flagging_rule.matching_values, ["OIEL"])

    def test_flagging_rule_can_change_verified_answer(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = FlagFactory(level=FlagLevels.GOOD, team=self.team)
        flagging_rule = self.create_flagging_rule(
            level="Good", flag=flag, team=self.team, matching_values=["ML1"], is_for_verified_goods_only="False"
        )

        data = {
            "is_for_verified_goods_only": "True",
        }

        url = reverse("flags:flagging_rule", kwargs={"pk": flagging_rule.id})
        self.client.put(url, data, **self.gov_headers)

        flagging_rule.refresh_from_db()

        self.assertTrue(flagging_rule.is_for_verified_goods_only)
