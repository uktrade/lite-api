import pytest

from django.urls import reverse
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.statuses.models import CaseStatus
from api.workflow.routing_rules.models import RoutingRule
from test_helpers.clients import DataTestClient


class RerunRoutingRulesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.queue = self.create_queue("A", self.team)
        self.other_queue = self.create_queue("B", self.team)
        self.url = reverse("cases:rerun_routing_rules", kwargs={"pk": self.case.id})
        self.routing_rule_1 = self.create_routing_rule(
            self.team.id,
            self.queue.id,
            tier=3,
            status_id=get_case_status_by_status(CaseStatusEnum.SUBMITTED).id,
            additional_rules=[],
        )

    def test_rules_rerun(self):
        self.case.queues.set([self.other_queue.id])

        response = self.client.put(self.url, {}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()
        self.assertEqual(self.case.queues.count(), 2)
        self.assertEqual(self.case.queues.first().id, self.queue.id)
