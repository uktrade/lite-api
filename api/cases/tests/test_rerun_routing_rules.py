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

    def test_rules_rerun_when_no_rules_are_applied_then_case_status_is_changed_and_audited(self):
        self.routing_rule_1.delete()

        # Delete all existing rules to ensure no rules are triggered
        for rule in RoutingRule.objects.all():
            rule.delete()

        self.case.queues.set([self.other_queue.id])

        response = self.client.put(self.url, {}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()

        # Case has been removed from queues
        self.assertEqual(self.case.queues.count(), 0)

        # Assert case status changed to all applicable statuses in correct order (ignoring initial submission status)
        exclude_payload = {
            "status": {
                "new": CaseStatusEnum.get_text(CaseStatusEnum.SUBMITTED),
                "old": CaseStatusEnum.get_text(CaseStatusEnum.DRAFT),
            }
        }

        actual_status_changes = (
            Audit.objects.filter(target_object_id=self.case.id, verb=AuditType.UPDATED_STATUS)
            .exclude(payload=exclude_payload)
            .order_by("created_at")
        )

        applicable_status_changes = CaseStatus.objects.filter(
            workflow_sequence__isnull=False,
            workflow_sequence__gt=CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED).workflow_sequence,
            workflow_sequence__lte=CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW).workflow_sequence,
        ).order_by("workflow_sequence")

        self.assertEqual(actual_status_changes.count(), applicable_status_changes.count())

        for index in range(len(applicable_status_changes)):
            self.assertEqual(
                actual_status_changes[index].payload["status"]["new"],
                CaseStatusEnum.get_text(applicable_status_changes[index].status),
            )

        # Assert the case status was finally set to Under Final Review (the last applicable status)
        self.assertEqual(self.case.status.status, CaseStatusEnum.UNDER_FINAL_REVIEW)
