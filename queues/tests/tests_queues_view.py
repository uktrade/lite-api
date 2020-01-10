from django.urls import reverse
from rest_framework import status

from queues.constants import ALL_CASES_QUEUE_ID
from queues.helpers import get_queue
from test_helpers.clients import DataTestClient


class QueuesViewTests(DataTestClient):
    def test_list_all_queues(self):
        """
        Tests that all queues are returned
        """
        url = reverse("queues:queues") + "?include_system_queues=True"

        response = self.client.get(url, **self.gov_headers)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["queues"]), 7)

    def test_list_queues(self):
        """
        Tests that all queues are returned
        """
        url = reverse("queues:queues")

        response = self.client.get(url, **self.gov_headers)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["queues"]), 1)

    def test_detail_system_queue(self):
        """
        View an individual system queue
        """
        queue = get_queue(ALL_CASES_QUEUE_ID)
        url = reverse("queues:queue", kwargs={"pk": queue.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["queue"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], queue.name)
        self.assertEqual(response_data["is_system_queue"], True)
        self.assertEqual(response_data["team"]["id"], str(queue.team.id))
        self.assertEqual(response_data["cases_count"], 0)

    def test_detail_queue(self):
        """
        View an individual queue
        """
        queue = self.create_queue("New Queue", self.team)
        url = reverse("queues:queue", kwargs={"pk": queue.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["queue"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], queue.name)
        self.assertEqual(response_data["is_system_queue"], False)
        self.assertEqual(response_data["team"]["id"], str(queue.team.id))
        self.assertEqual(response_data["cases_count"], 0)
