from django.urls import reverse
from rest_framework import status

from api.queues.tests.factories import QueueFactory
from test_helpers.clients import DataTestClient


class QueuesCreateTests(DataTestClient):

    url = reverse("queues:queues")

    def test_create_queue(self):
        data = {
            "name": "new_queue",
            "team": self.team.id,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()["queue"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["name"], data["name"])
        self.assertEqual(response_data["team"], str(self.team.id))

    def test_create_queue_with_countersigning_queue(self):
        countersigning_queue = QueueFactory(name="countersigning_queue", team=self.team)
        data = {
            "name": "new_queue",
            "team": self.team.id,
            "countersigning_queue": countersigning_queue.id,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()["queue"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["name"], data["name"])
        self.assertEqual(response_data["team"], str(self.team.id))
        self.assertEqual(response_data["countersigning_queue"], str(countersigning_queue.id))
