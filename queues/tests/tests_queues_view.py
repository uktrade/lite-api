from django.urls import reverse
from rest_framework import status

from queues.constants import ALL_CASES_QUEUE_ID
from queues.helpers import get_queue
from test_helpers.clients import DataTestClient


class QueuesViewTests(DataTestClient):
    def test_list_queues(self):
        """
        Tests that all queues are returned
        """
        url = reverse("queues:queues")

        response = self.client.get(url, **self.gov_headers)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 1)

    def test_detail_queue(self):
        """
        View an individual queue
        """
        queue = self.create_queue("New Queue", self.team)
        url = reverse("queues:queue", kwargs={"pk": queue.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualIgnoreType(response_data["id"], queue.id)
        self.assertEqual(response_data["name"], queue.name)
        self.assertEqual(response_data["is_system_queue"], False)
