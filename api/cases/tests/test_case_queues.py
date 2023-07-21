import uuid

from django.urls import reverse
from rest_framework import status

from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from lite_content.lite_api.strings import Cases
from test_helpers.clients import DataTestClient


class AssignQueuesToCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.url = reverse("cases:queues", kwargs={"pk": self.case.id})
        self.queues = [
            self.create_queue("Queue 1", self.team),
            self.create_queue("Queue 2", self.team),
            self.create_queue("Queue 3", self.team),
        ]

    def test_set_queues_successful(self):
        data = {"queues": [queue.id for queue in self.queues]}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(response.json()["queues"]), sorted([str(id) for id in data["queues"]]))
        self.assertEqual(set(self.case.queues.values_list("id", flat=True)), set(data["queues"]))
        self.assertTrue(Audit.objects.filter(verb=AuditType.MOVE_CASE).exists())
        self.assertFalse(Audit.objects.filter(verb=AuditType.REMOVE_CASE).exists())

    def test_set_queues_with_initial_data_successful(self):
        self.case.queues.set(self.queues[:2])
        data = {"queues": [self.queues[2].id]}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(response.json()["queues"]), sorted([str(id) for id in data["queues"]]))
        self.assertEqual(set(self.case.queues.values_list("id", flat=True)), set(data["queues"]))
        self.assertTrue(Audit.objects.filter(verb=AuditType.MOVE_CASE).exists())
        self.assertTrue(Audit.objects.filter(verb=AuditType.REMOVE_CASE).exists())

    def test_remove_queues_successful(self):
        self.case.queues.set(self.queues)
        data = {"queues": [queue.id for queue in self.queues[:2]]}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(response.json()["queues"]), sorted([str(id) for id in data["queues"]]))
        self.assertEqual(set(self.case.queues.values_list("id", flat=True)), set(data["queues"]))
        self.assertFalse(Audit.objects.filter(verb=AuditType.MOVE_CASE).exists())
        self.assertTrue(Audit.objects.filter(verb=AuditType.REMOVE_CASE).exists())

    def test_remove_all_queues_successful(self):
        self.case.queues.set(self.queues)
        data = {"queues": []}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.case.queues.exists())
        self.assertFalse(Audit.objects.filter(verb=AuditType.MOVE_CASE).exists())
        self.assertTrue(Audit.objects.filter(verb=AuditType.REMOVE_CASE).exists())

    def test_set_case_queue_not_found_failure(self):
        random_id = uuid.uuid4()
        data = {"queues": [random_id]}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"]["queues"], [f"{Cases.Queue.NOT_FOUND}['{str(random_id)}']"])

    def test_case_remove_all_case_assignments(self):
        self.case.queues.set([self.queue])
        self.create_case_assignment(self.queue, self.case, [self.gov_user])

        self.assertEqual(self.case.queues.count(), 1)
        self.assertEqual(self.case.case_assignments.count(), 1)

        self.case.remove_all_case_assignments()
        self.case.refresh_from_db()

        self.assertEqual(self.case.queues.count(), 0)
        self.assertEqual(self.case.case_assignments.count(), 0)
