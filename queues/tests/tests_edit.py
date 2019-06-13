from django.urls import reverse
from rest_framework import status

from queues.models import Queue
from test_helpers.clients import DataTestClient


class QueueEditTests(DataTestClient):

    def tests_edit_queue(self):
        data = {
            'id': '00000000-0000-0000-0000-000000000001',
            'name': 'Modified queue',
            # 'team': '',
        }
        url = reverse('queues:queue', kwargs={'pk': data['id']})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Queue.objects.filter(name='Modified queue').count(), 1)
