from django.urls import reverse
from rest_framework import status

from cases.models import CaseType
from flags.enums import FlagLevels
from static.countries.models import Country
from static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from workflow.routing_rules.enum import RoutingRulesAdditionalFields


class RoutingRuleCreationTests(DataTestClient):
    def test_all_data_works(self):
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

        print(routing_rule)
