from django.urls import reverse
from rest_framework import status

from api.cases.models import CaseAssignmentSla, CaseAssignment
from test_helpers.clients import DataTestClient
from api.users.tests.factories import GovUserFactory


class DataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation, "Example Application")
        self.queue.cases.add(self.case)
        CaseAssignmentSla.objects.create(sla_days=4, queue=self.queue, case=self.case)

        # Create CaseAssignment
        user = GovUserFactory(
            baseuser_ptr__email="john@dov.uk",
            baseuser_ptr__first_name="John",
            baseuser_ptr__last_name="Conam",
            team=self.team,
        )
        CaseAssignment.objects.create(queue=self.queue, case=self.case, user=user)

    def test_case_assignment(self):
        url = reverse("data_workspace:dw-case-assignment-list")

        # Check GET
        expected_fields = {"user", "case"}
        expected_user_fields = {"id", "first_name", "last_name", "email", "team"}
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(set(results[0].keys()), expected_fields)
        self.assertEqual(set(results[0]["user"].keys()), expected_user_fields)

        # Check OPTIONS
        expected_fields = {"user", "case"}
        expected_case_fields = {"type", "required", "read_only", "label"}
        expected_user_fields = {"type", "required", "read_only", "label", "children"}
        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(set(options.keys()), expected_fields)
        self.assertEqual(set(options["case"].keys()), expected_case_fields)
        self.assertEqual(set(options["user"].keys()), expected_user_fields)

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
