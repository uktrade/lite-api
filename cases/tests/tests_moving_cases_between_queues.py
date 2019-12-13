from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity
from test_helpers.clients import DataTestClient


class MoveCasesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_clc_query("Query", self.organisation)
        self.url = reverse("cases:case", kwargs={"pk": self.case.id})
        self.queues = [
            self.create_queue("Queue 1", self.team),
            self.create_queue("Queue 2", self.team),
            self.create_queue("Queue 3", self.team),
        ]

    def test_move_case_successful(self):
        data = {"queues": [queue.id for queue in self.queues]}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(self.case.queues.values_list("id", flat=True)), set(data["queues"]))

    def test_add_and_remove_case_to_queue(self):
        queues_data = {"queues": [queue.id for queue in self.queues]}

        response = self.client.put(self.url, data=queues_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(self.case.queues.values_list("id", flat=True)), set(queues_data["queues"]),
        )

        no_queues_data = {"queues": []}

        response = self.client.put(self.url, data=no_queues_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(self.case.queues.values_list("id", flat=True)), set(no_queues_data["queues"]),
        )

    def test_case_activity_created(self):
        self.assertEqual(CaseActivity.objects.all().count(), 0)
        queues_data = {"queues": [queue.id for queue in self.queues]}

        self.client.put(self.url, data=queues_data, **self.gov_headers)

        self.assertEqual(CaseActivity.objects.all().count(), 1)
        case_activities = CaseActivity.objects.all().values_list("type", flat=True)
        self.assertTrue(CaseActivityType.MOVE_CASE in case_activities)

        no_queues_data = {"queues": []}

        self.client.put(self.url, data=no_queues_data, **self.gov_headers)

        self.assertEqual(CaseActivity.objects.all().count(), 2)
        case_activities = CaseActivity.objects.all().values_list("type", flat=True)
        self.assertTrue(CaseActivityType.REMOVE_CASE in case_activities)

    @parameterized.expand(
        [
            # Invalid Queues
            [{"queues": "Not an array"}],
            [{"queues": ["00000000-0000-0000-0000-000000000002"]}],
            [{"queues": ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002",]}],
        ]
    )
    def test_move_case_failure(self, data):
        existing_queues = set(self.case.queues.values_list("id", flat=True))

        response = self.client.put(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(self.case.queues.values_list("id", flat=True)), existing_queues)
