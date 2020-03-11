from django.urls import reverse
from rest_framework import status

from flags.models import FlaggingRule
from test_helpers.clients import DataTestClient


class FlaggingRulesCreateTest(DataTestClient):

    url = reverse("flags:flagging_rules")

    def test_gov_user_can_create_flagging_rule(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = self.create_flag("test", "Case", self.team)

        data = {"level": "Case", "flag": str(flag.id), "matching_value": "SIEL"}

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["level"], "Case")
        self.assertEqual(response_data["flag"], str(flag.id))
        self.assertEqual(response_data["matching_value"], "SIEL")

    def test_create_flagging_rule_failure_duplicate(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("test", "Case", self.team)
        FlaggingRule(flag=flag, team=self.team, matching_value="SIEL", level="Case").save()

        response = self.client.post(
            self.url, {"level": "Case", "flag": str(flag.id), "matching_value": "SIEL"}, **self.gov_headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
