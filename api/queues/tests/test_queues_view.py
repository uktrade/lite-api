from django.urls import reverse
from rest_framework import status

from api.queues.constants import SYSTEM_QUEUES
from api.queues.models import Queue
from test_helpers.clients import DataTestClient


class QueuesViewTests(DataTestClient):
    def test_list_work_queues(self):
        """
        Tests that all queues are returned
        """
        url = reverse("queues:queues")

        response = self.client.get(url, **self.gov_headers)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 25)
        self.assertTrue(Queue.objects.filter(pk=data["results"][0]["id"]).exists())

    def test_list_all_queues(self):
        """
        Tests that all queues are returned
        """
        url = reverse("queues:queues") + "?include_system=True"

        response = self.client.get(url, **self.gov_headers)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 54)
        for queue in data:
            queue_exists = queue["id"] in SYSTEM_QUEUES.keys() or Queue.objects.filter(pk=queue["id"]).exists()
            self.assertTrue(queue_exists)

    def test_filter_queues_by_name(self):
        url = reverse("queues:queues") + "?name=" + self.queue.name

        response = self.client.get(url, **self.gov_headers)
        data = response.json()["results"]

        self.assertTrue(self.queue.name in [queue["name"] for queue in data])

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
