from django.urls import reverse
from functools import partial
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class DataWorkspaceAuditMoveCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("data_workspace:dw-audit-move-case-list")
        case = self.create_standard_application_case(self.organisation, "Test Application")
        # Audit events are only created for non-draft cases
        case.status = get_case_status_by_status(CaseStatusEnum.OPEN)
        case.save()
        self.create_audit = partial(
            super().create_audit, verb=AuditType.MOVE_CASE, actor=self.gov_user, target=case.get_case()
        )

        self.create_audit(payload={"queues": "Initial Queue"})
        self.create_audit(verb=AuditType.CREATED_USER_ADVICE)

    def test_audit_move_case(self):
        expected_fields = ("created_at", "user", "case", "queue")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(tuple(results[0].keys()), expected_fields)
        self.assertEqual(results[0]["queue"], str(self.queue.pk))

        response = self.client.options(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_payload_multiple_queues(self):
        queue1 = self.create_queue("MOD - DSR Cases to Review", self.team)
        queue2 = self.create_queue("MOD - WECA Cases to Review", self.team)
        # Create a single audit record with multiple queues in the payload
        self.create_audit(payload={"queues": ["MOD - DSR Cases to Review", "MOD - WECA Cases to Review"]})

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["queue"], str(self.queue.pk))
        # The record with multiple queues should have been split into separate entries.
        self.assertEqual(results[1]["queue"], str(queue1.pk))
        self.assertEqual(results[2]["queue"], str(queue2.pk))


class DataWorkspaceUpdatedStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("data_workspace:dw-audit-updated-status-list")
        case = self.create_standard_application_case(self.organisation, "Test Application")
        # Audit events are only created for non-draft cases
        case.status = get_case_status_by_status(CaseStatusEnum.OPEN)
        # This will generate an updated status audit entry.
        case.save()
        self.create_audit = partial(
            super().create_audit, verb=AuditType.UPDATED_STATUS, actor=self.gov_user, target=case.get_case()
        )

        self.create_audit(verb=AuditType.CREATED_USER_ADVICE)

    def test_audit_updated_status(self):
        expected_fields = ("created_at", "user", "case", "status")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(tuple(results[0].keys()), expected_fields)
        self.assertEqual(results[0]["status"], "Submitted")

        response = self.client.options(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)
