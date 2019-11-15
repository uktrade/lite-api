from django.urls import reverse
from rest_framework import status

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
