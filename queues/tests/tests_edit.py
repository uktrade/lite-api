from django.urls import reverse
from rest_framework import status

from queues.tests.factories import QueueFactory
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
