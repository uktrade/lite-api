from django.urls import reverse
from functools import partial
from rest_framework import status

from freezegun import freeze_time

from api.audit_trail.enums import AuditType
from api.licences.models import LicenceStatus
from api.licences.tests.factories import StandardLicenceFactory
from api.queues.models import Queue
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class DataWorkspaceAuditMoveCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("data_workspace:v1:dw-audit-move-case-list")
        self.case = self.create_standard_application_case(self.organisation, "Test Application")
        # Audit events are only created for non-draft cases
        self.case.status = get_case_status_by_status(CaseStatusEnum.OPEN)
        self.case.save()
        self.create_audit = partial(
            super().create_audit, verb=AuditType.MOVE_CASE, actor=self.gov_user, target=self.case.get_case()
        )

    @freeze_time("2023-11-03 12:00:00")
    def test_audit_move_case(self):
        queue = Queue.objects.get(name="Initial Queue")
        self.create_audit(payload={"queues": queue.name})
        self.create_audit(verb=AuditType.CREATED_USER_ADVICE)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(
            results,
            [
                {
                    "created_at": "2023-11-03T12:00:00Z",
                    "user": str(self.gov_user.pk),
                    "case": str(self.case.pk),
                    "queue": str(queue.pk),
                }
            ],
        )

    @freeze_time("2023-11-03 12:00:00")
    def test_payload_multiple_queues(self):
        queue = queue = Queue.objects.get(name="Initial Queue")
        self.create_audit(payload={"queues": queue.name})
        queue1 = self.create_queue("MOD - DSR Cases to Review", self.team)
        queue2 = self.create_queue("MOD - WECA Cases to Review", self.team)
        # Create a single audit record with multiple queues in the payload
        self.create_audit(payload={"queues": [queue1.name, queue2.name]})

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(
            results,
            [
                {
                    "created_at": "2023-11-03T12:00:00Z",
                    "user": str(self.gov_user.pk),
                    "case": str(self.case.pk),
                    "queue": str(queue.pk),
                },
                {
                    "created_at": "2023-11-03T12:00:00Z",
                    "user": str(self.gov_user.pk),
                    "case": str(self.case.pk),
                    "queue": str(queue1.pk),
                },
                {
                    "created_at": "2023-11-03T12:00:00Z",
                    "user": str(self.gov_user.pk),
                    "case": str(self.case.pk),
                    "queue": str(queue2.pk),
                },
            ],
        )


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
