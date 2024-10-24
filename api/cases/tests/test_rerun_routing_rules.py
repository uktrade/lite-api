import uuid

from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from api.cases.enums import CaseTypeSubTypeEnum
from api.staticdata.statuses.enums import CaseStatusEnum

from lite_routing.routing_rules_internal.registries import RoutingRulesRegister

from test_helpers.clients import DataTestClient


class RerunRoutingRulesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.queue = self.create_queue("A", self.team)
        self.other_queue = self.create_queue("B", self.team)
        self.url = reverse("cases:rerun_routing_rules", kwargs={"pk": self.case.id})

    @patch(
        "lite_routing.routing_rules_internal.routing_engine.routing_rules",
        new_callable=RoutingRulesRegister,
    )
    def test_rules_rerun(self, mock_routing_rules):
        self.case.queues.set([self.other_queue.id])

        @mock_routing_rules.register(
            rule_id=uuid.uuid4(),
            case_sub_type=CaseTypeSubTypeEnum.STANDARD,
            case_status=CaseStatusEnum.SUBMITTED,
            team=self.team.id,
            tier=3,
            queue=self.queue.id,
        )
        def rule(case):
            return True

        response = self.client.put(self.url, {}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()
        self.assertEqual(self.case.queues.count(), 1)
        self.assertEqual(self.case.queues.get().id, self.queue.id)
