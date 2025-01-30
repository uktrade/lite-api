from django.urls import reverse
from functools import partial
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.licences.models import LicenceStatus
from api.licences.tests.factories import StandardLicenceFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum


class DataWorkspaceAuditMoveCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("data_workspace:v1:dw-audit-move-case-list")
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


class DataWorkspaceAuditUpdatedCaseStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("data_workspace:v1:dw-audit-updated-status-list")
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
        self.assertEqual(results[0]["status"], "submitted")

        response = self.client.options(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)


class DataWorkspaceAuditBulkApprovalRecommendationTests(DataTestClient):

    def test_audit_bulk_approval_recommendation(self):
        cases = [self.create_standard_application_case(self.organisation, "Test Application") for _ in range(5)]
        for case in cases:
            case.status = get_case_status_by_status(CaseStatusEnum.OGD_ADVICE)
            case.save()

        data = {
            "cases": [str(case.id) for case in cases],
            "advice": {
                "text": "No concerns",
                "proviso": "",
                "note": "",
                "footnote_required": False,
                "footnote": "",
                "team": TeamIdEnum.MOD_CAPPROT,
            },
        }
        url = reverse("caseworker_queues:bulk_approval", kwargs={"pk": QueuesEnum.MOD_CAPPROT})
        response = self.client.post(url, data=data, **self.gov_headers)
        assert response.status_code == 201

        expected_fields = ("id", "created_at", "user", "case", "queue")

        url = reverse("data_workspace:v1:dw-audit-bulk-approval-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 5)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)


class DataWorkspaceAuditUpdatedLicenceStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("data_workspace:v1:dw-audit-licence-updated-status-list")
        case = self.create_standard_application_case(self.organisation, "Test Application")
        licence = StandardLicenceFactory(case=case, status=LicenceStatus.ISSUED)

    def test_audit_updated_status(self):
        expected_fields = ("created_at", "user", "case", "licence", "status")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(tuple(results[0].keys()), expected_fields)
        self.assertEqual(results[0]["status"], "issued")

        response = self.client.options(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)
