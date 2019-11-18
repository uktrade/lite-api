from django.urls import reverse
from rest_framework import status

from queues.models import Queue
from test_helpers.clients import DataTestClient


class QueueEditTests(DataTestClient):
    def test_edit_queue(self):
        data = {
            "id": self.queue.id,
            "name": "Modified queue",
        }

        url = reverse("queues:queue", kwargs={"pk": data["id"]})
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Queue.objects.filter(name=data["name"]).count(), 1)
