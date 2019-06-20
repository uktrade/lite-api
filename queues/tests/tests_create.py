from django.urls import reverse
from rest_framework import status

from queues.models import Queue
from teams.models import Team
from test_helpers.clients import DataTestClient


class QueueCreateTests(DataTestClient):

    url = reverse('queues:queues')
    existing_queues_count = Queue.objects.all().count()

    def tests_create_queue(self):
        data = {
            'name': 'new_queue',
            'team': Team.objects.get().id
        }
        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Note: A queue "New Cases" is created by default
        self.assertEqual(Queue.objects.all().count(), self.existing_queues_count + 1)

        queue = Queue.objects.get(pk=response.json().get('queue').get('id'))

        self.assertEqual(queue.team.id, Team.objects.get().id)

