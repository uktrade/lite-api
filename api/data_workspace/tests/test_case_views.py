from django.urls import reverse
from rest_framework import status

from api.cases.models import CaseAssignmentSla, CaseAssignment
from test_helpers.clients import DataTestClient
from test_helpers.assertions import is_uuid_as_string
from api.users.tests.factories import GovUserFactory
from api.cases.tests.factories import EcjuQueryFactory


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

        expected_fields = {"user", "case", "id", "queue", "created_at", "updated_at"}
        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        actions_get = payload["actions"]["GET"]
        self.assertEqual(set(actions_get.keys()), expected_fields)

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

    def test_ecju_queries(self):
        EcjuQueryFactory()
        url = reverse("data_workspace:dw-ecju-query-list")
        expected_fields = {
            "raised_by_user",
            "id",
            "updated_at",
            "question",
            "response",
            "query_type",
            "case",
            "team",
            "responded_by_user",
            "responded_at",
            "created_at",
        }
        allowed_actions = {"HEAD", "OPTIONS", "GET"}

        # Test GET
        payload = self.client.get(url).json()
        assert payload["count"] == 1
        first_result = payload["results"][0]
        assert set(first_result.keys()) == expected_fields

        # Ensure keys are UUIDs
        assert is_uuid_as_string(first_result["case"])
        assert is_uuid_as_string(first_result["team"])
        assert is_uuid_as_string(first_result["raised_by_user"])

        # Test schema actions advertised are correct
        options = self.client.options(url).json()
        assert set(options["actions"].keys()) == allowed_actions
        assert set(options["actions"]["GET"].keys()) == expected_fields
