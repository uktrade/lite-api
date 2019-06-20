from django.urls import reverse
from rest_framework import status

from queues.models import Queue
from queues.tests.tests_consts import EXISTING_QUEUE_ID
from test_helpers.clients import DataTestClient


class QueueEditTests(DataTestClient):

    def tests_edit_queue(self):
        data = {
            'id': EXISTING_QUEUE_ID,
            'name': 'Modified queue',
        }
        url = reverse('queues:queue', kwargs={'pk': data['id']})
        response = self.client.put(url, data, format='json', **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Queue.objects.filter(name='Modified queue').count(), 1)
