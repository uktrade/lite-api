from django.urls import reverse
from rest_framework import status

from queues.models import Queue
from test_helpers.clients import DataTestClient


class QueueCreateTests(DataTestClient):

    url = reverse('queues:queues')

    def tests_create_queue(self):
        existing_queues_count = Queue.objects.all().count()

        data = {
            'name': 'new_queue',
            'team': self.team.id,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()['queue']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Queue.objects.all().count(), existing_queues_count + 1)
        self.assertEqual(response_data['name'], data['name'])
        self.assertEqual(response_data['team'], str(self.team.id))

