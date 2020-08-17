from django.urls import reverse
from rest_framework import status

from api.cases.models import CaseType
from api.flags.enums import FlagLevels
from api.staticdata.countries.models import Country
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from api.workflow.routing_rules.enum import RoutingRulesAdditionalFields


class RoutingRuleCreationTests(DataTestClient):
    def test_all_data_works(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)
        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": [*[k for k, v in RoutingRulesAdditionalFields.choices]],
            "user": self.gov_user.id,
            "flags": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:list")

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        routing_rule = response.json()

        self.assertEqual(routing_rule["team"]["id"], str(self.team.id))
        self.assertEqual(routing_rule["queue"]["id"], str(self.queue.id))
        self.assertEqual(routing_rule["tier"], data["tier"])
        self.assertEqual(routing_rule["status"]["id"], str(data["status"]))
        self.assertEqual(routing_rule["user"]["id"], str(self.gov_user.id))
        self.assertEqual(routing_rule["flags"][0]["id"], str(flag.id))
        self.assertEqual(routing_rule["case_types"][0]["id"], str(data["case_types"][0]))
        self.assertEqual(routing_rule["country"]["id"], str(data["country"]))

    def test_users_only_additional_rule(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)
        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": [RoutingRulesAdditionalFields.USERS],
            "user": self.gov_user.id,
            "flags": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:list")

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        routing_rule = response.json()

        self.assertEqual(routing_rule["team"]["id"], str(self.team.id))
        self.assertEqual(routing_rule["queue"]["id"], str(self.queue.id))
        self.assertEqual(routing_rule["tier"], data["tier"])
        self.assertEqual(routing_rule["status"]["id"], str(data["status"]))
        self.assertEqual(routing_rule["user"]["id"], str(self.gov_user.id))
        self.assertEqual(routing_rule["flags"], [])
        self.assertEqual(routing_rule["case_types"], [])
        self.assertIsNone(routing_rule["country"])

    def test_country_only_additional_rule(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)
        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": [RoutingRulesAdditionalFields.COUNTRY],
            "user": self.gov_user.id,
            "flags": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:list")

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        routing_rule = response.json()

        self.assertEqual(routing_rule["team"]["id"], str(self.team.id))
        self.assertEqual(routing_rule["queue"]["id"], str(self.queue.id))
        self.assertEqual(routing_rule["tier"], data["tier"])
        self.assertEqual(routing_rule["status"]["id"], str(data["status"]))
        self.assertIsNone(routing_rule["user"])
        self.assertEqual(routing_rule["flags"], [])
        self.assertEqual(routing_rule["case_types"], [])
        self.assertEqual(routing_rule["country"]["id"], str(data["country"]))

    def test_case_type_only_additional_rule(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)
        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": [RoutingRulesAdditionalFields.CASE_TYPES],
            "user": self.gov_user.id,
            "flags": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:list")

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        routing_rule = response.json()

        self.assertEqual(routing_rule["team"]["id"], str(self.team.id))
        self.assertEqual(routing_rule["queue"]["id"], str(self.queue.id))
        self.assertEqual(routing_rule["tier"], data["tier"])
        self.assertEqual(routing_rule["status"]["id"], str(data["status"]))
        self.assertIsNone(routing_rule["user"])
        self.assertEqual(routing_rule["flags"], [])
        self.assertEqual(routing_rule["case_types"][0]["id"], str(data["case_types"][0]))
        self.assertIsNone(routing_rule["country"])

    def test_flags_only_additional_rule(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)
        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": [RoutingRulesAdditionalFields.FLAGS],
            "user": self.gov_user.id,
            "flags": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:list")

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        routing_rule = response.json()

        self.assertEqual(routing_rule["team"]["id"], str(self.team.id))
        self.assertEqual(routing_rule["queue"]["id"], str(self.queue.id))
        self.assertEqual(routing_rule["tier"], data["tier"])
        self.assertEqual(routing_rule["status"]["id"], str(data["status"]))
        self.assertIsNone(routing_rule["user"])
        self.assertEqual(routing_rule["flags"][0]["id"], str(flag.id))
        self.assertEqual(routing_rule["case_types"], [])
        self.assertIsNone(routing_rule["country"])

    def test_no_additional_rule(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)
        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": [],
            "user": self.gov_user.id,
            "flags": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:list")

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        routing_rule = response.json()

        self.assertEqual(routing_rule["team"]["id"], str(self.team.id))
        self.assertEqual(routing_rule["queue"]["id"], str(self.queue.id))
        self.assertEqual(routing_rule["tier"], data["tier"])
        self.assertEqual(routing_rule["status"]["id"], str(data["status"]))
        self.assertIsNone(routing_rule["user"])
        self.assertEqual(routing_rule["flags"], [])
        self.assertEqual(routing_rule["case_types"], [])
        self.assertIsNone(routing_rule["country"])

    def test_fail_bad_additional_rule(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)
        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": ["blah"],
            "user": self.gov_user.id,
            "flags": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:list")

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_negative_tier(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)
        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": -1,
            "additional_rules": [],
            "user": self.gov_user.id,
            "flags": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:list")

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_no_permission(self):
        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)
        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": [],
            "user": self.gov_user.id,
            "flags": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:list")

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
