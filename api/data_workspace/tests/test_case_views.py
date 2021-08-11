from django.urls import reverse
from rest_framework import status

from api.cases.models import CaseAssignmentSla
from test_helpers.clients import DataTestClient


class DataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation, "Example Application")
        self.queue.cases.add(self.case)
        CaseAssignmentSla.objects.create(sla_days=4, queue=self.queue, case=self.case)

    def test_case_assignment_slas(self):
        url = reverse("data_workspace:dw-case-assignment-sla-list")
        expected_fields = ("id", "sla_days", "queue", "case")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_case_types(self):
        url = reverse("data_workspace:dw-case-type-list")
        expected_fields = ("id", "reference", "type", "sub_type")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_case_queues(self):
        url = reverse("data_workspace:dw-case-queue-list")
        expected_fields = ("id", "created_at", "updated_at", "case", "queue")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)
