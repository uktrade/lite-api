from django.urls import reverse
from rest_framework import status

from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from lite_content.lite_api.strings import Cases
from api.workflow.routing_rules.enum import RoutingRulesAdditionalFields


class CaseAssignmentTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.queue = self.create_queue("A", self.team)
        self.other_team = self.create_team("Other")
        self.other_user = self.create_gov_user("test@gmail.com", self.other_team)
        self.other_queue = self.create_queue("B", self.other_team)
        self.url = reverse("cases:assigned_queues", kwargs={"pk": self.case.id})

    def test_get_assigned_cases_success(self):
        self.create_case_assignment(self.queue, self.case, users=[self.gov_user])

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["queues"], [{"id": str(self.queue.id), "name": self.queue.name}])

    def test_get_assigned_cases_ignores_other_users_queues_success(self):
        self.create_case_assignment(self.other_queue, self.case, users=[self.other_user])

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["queues"], [])

    def test_put_unassign_queues_success(self):
        self.create_case_assignment(self.queue, self.case, users=[self.gov_user])

        response = self.client.put(self.url, **self.gov_headers, data={"queues": [self.queue.id]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["queues_removed"], [self.queue.name])
        self.assertTrue(Audit.objects.filter(verb=AuditType.UNASSIGNED_QUEUES).exists())

    def test_put_unassign_different_case_success(self):
        case = self.create_standard_application_case(self.organisation)
        self.create_case_assignment(self.queue, case, users=[self.gov_user])

        response = self.client.put(self.url, **self.gov_headers, data={"queues": [self.queue.id]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["queues_removed"], [])
        self.assertFalse(Audit.objects.filter(verb=AuditType.UNASSIGNED_QUEUES).exists())

    def test_put_unassign_different_queue_success(self):
        self.create_case_assignment(self.other_queue, self.case, users=[self.gov_user])

        response = self.client.put(self.url, **self.gov_headers, data={"queues": [self.queue.id]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["queues_removed"], [])
        self.assertFalse(Audit.objects.filter(verb=AuditType.UNASSIGNED_QUEUES).exists())

    def test_put_unassign_different_user_success(self):
        self.create_case_assignment(self.queue, self.case, users=[self.other_user])

        response = self.client.put(self.url, **self.gov_headers, data={"queues": [self.queue.id]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["queues_removed"], [])
        self.assertFalse(Audit.objects.filter(verb=AuditType.UNASSIGNED_QUEUES).exists())

    def test_put_unassign_no_assignments_success(self):
        response = self.client.put(self.url, **self.gov_headers, data={"queues": [self.queue.id]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["queues_removed"], [])

    def test_put_unassign_no_assignments_multiple_queues_failure(self):
        response = self.client.put(self.url, **self.gov_headers, data={"queues": [self.queue.id, self.other_queue.id]})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"queues": [Cases.UnassignQueues.NOT_ASSIGNED_MULTIPLE_QUEUES]}})

    def test_put_unassign_no_assignments_non_team_queue_failure(self):
        response = self.client.put(self.url, **self.gov_headers, data={"queues": [self.other_queue.id]})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"queues": [Cases.UnassignQueues.INVALID_TEAM]}})

    def test_put_unassign_no_queues_failure(self):
        response = self.client.put(self.url, **self.gov_headers, data={"queues": []})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"queues": [Cases.UnassignQueues.NO_QUEUES]}})
