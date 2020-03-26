from django.test import tag
from django.urls import reverse
from rest_framework import status

from test_helpers.clients import PerformanceTestClient
from parameterized import parameterized


@tag("destructive")
class FlaggingRulesPerformanceTests(PerformanceTestClient):
    url = reverse("flags:flagging_rules")

    def _create_flagging_rule_request(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = self.create_flag("test", "Case", self.team)
        data = {"level": "Case", "flag": str(flag.id), "matching_value": "SIEL"}

        response = self.client.post(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @parameterized.expand([(10,), (100,), (1000,)])
    def test_create_flagging_rules_open_cases(self, open_cases_count):
        """
        Tests the performance of the 'flags/rules/' endpoint
        """
        for i in range(open_cases_count):
            self.create_standard_application_case(organisation=self.organisation)

        print(f"open_cases: {open_cases_count}")
        self.timeit(self._create_flagging_rule_request)
