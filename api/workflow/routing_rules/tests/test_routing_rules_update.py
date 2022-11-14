import pytest as pytest
from django.urls import reverse
from rest_framework import status

from api.cases.models import CaseType
from api.flags.enums import FlagLevels
from api.staticdata.countries.models import Country
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from api.workflow.routing_rules.enum import RoutingRulesAdditionalFields


@pytest.mark.skip("Legacy routing rules obsolete as of C5")
class RoutingRuleUpdateTests(DataTestClient):
    def test_update_to_have_all_data(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)

        routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[],
        )

        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": [*[k for k, v in RoutingRulesAdditionalFields.choices]],
            "user": self.gov_user.pk,
            "flags_to_include": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:detail", kwargs={"pk": routing_rule.id})

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        routing_rule = response.json()

        self.assertEqual(routing_rule["team"]["id"], str(self.team.id))
        self.assertEqual(routing_rule["queue"]["id"], str(self.queue.id))
        self.assertEqual(routing_rule["tier"], data["tier"])
        self.assertEqual(routing_rule["status"]["id"], str(data["status"]))
        self.assertEqual(routing_rule["user"]["id"], str(self.gov_user.pk))
        self.assertEqual(routing_rule["flags_to_include"][0]["id"], str(flag.id))
        self.assertEqual(routing_rule["case_types"][0]["id"], str(data["case_types"][0]))
        self.assertEqual(routing_rule["country"]["id"], str(data["country"]))

    def test_remove_additional_rules_works(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = self.create_flag("flag", FlagLevels.GOOD, self.team)

        routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[*[k for k, v in RoutingRulesAdditionalFields.choices]],
        )

        data = {
            "team": self.team.id,
            "queue": self.queue.id,
            "tier": 1,
            "additional_rules": [],
            "user": self.gov_user.pk,
            "flags_to_include": [flag.id],
            "status": CaseStatus.objects.first().id,
            "case_types": [CaseType.objects.first().id],
            "country": Country.objects.first().id,
        }

        url = reverse("routing_rules:detail", kwargs={"pk": routing_rule.id})

        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        routing_rule = response.json()

        self.assertEqual(routing_rule["team"]["id"], str(self.team.id))
        self.assertEqual(routing_rule["queue"]["id"], str(self.queue.id))
        self.assertEqual(routing_rule["tier"], data["tier"])
        self.assertEqual(routing_rule["status"]["id"], str(data["status"]))
        self.assertIsNone(routing_rule["user"])
        self.assertEqual(routing_rule["flags_to_include"], [])
        self.assertEqual(routing_rule["case_types"], [])
        self.assertIsNone(routing_rule["country"])


@pytest.mark.skip("Legacy routing rules obsolete as of C5")
class RoutingRuleStatusChangeTests(DataTestClient):
    def test_deactivate(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[*[k for k, v in RoutingRulesAdditionalFields.choices]],
        )

        self.assertEqual(routing_rule.active, True)

        url = reverse("routing_rules:active_status", kwargs={"pk": routing_rule.id})

        response = self.client.put(url, {"status": "deactivate"}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        routing_rule.refresh_from_db()

        self.assertEqual(routing_rule.active, False)

    def test_activate(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        routing_rule = self.create_routing_rule(
            team_id=self.team.id,
            queue_id=self.queue.id,
            tier=5,
            status_id=CaseStatus.objects.last().id,
            additional_rules=[*[k for k, v in RoutingRulesAdditionalFields.choices]],
        )

        routing_rule.active = False
        routing_rule.save()

        self.assertEqual(routing_rule.active, False)

        url = reverse("routing_rules:active_status", kwargs={"pk": routing_rule.id})

        response = self.client.put(url, {"status": "reactivate"}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        routing_rule.refresh_from_db()

        self.assertEqual(routing_rule.active, True)
