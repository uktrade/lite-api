from django.urls import reverse
from rest_framework import status

from api.queues.tests.factories import QueueFactory
from test_helpers.clients import DataTestClient


class QueueEditTests(DataTestClient):
    def test_edit_queue(self):
        data = {
            "id": self.queue.id,
            "name": "Modified queue",
            "countersigning_queue": QueueFactory(name="other_queue", team=self.team).id,
        }

        url = reverse("queues:queue", kwargs={"pk": data["id"]})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.queue.refresh_from_db()
        self.assertEqual(self.queue.name, data["name"])
        self.assertEqual(self.queue.countersigning_queue_id, data["countersigning_queue"])

    def test_edit_queue_with_its_own_queue_id_as_countersigning_queue_fail(self):
        data = {
            "id": self.queue.id,
            "name": "Modified queue",
            "countersigning_queue": self.queue.id,
        }

        url = reverse("queues:queue", kwargs={"pk": data["id"]})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
