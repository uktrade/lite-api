from django.urls import reverse
from rest_framework import status

from queues.models import Queue
from teams.models import Team
from test_helpers.clients import DataTestClient


class QueueCreateTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.url = reverse('queues:queues')

    def tests_create_queue(self):

        existing_queues_count = Queue.objects.all().count()
        data = {
            'name': 'new_queue',
            'team': str(Team.objects.filter(name="Admin")[0].id),
            'cases': {}
        }
        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Note: A queue "New Cases" is created by default
        self.assertEqual(Queue.objects.all().count(), existing_queues_count + 1)
        self.assertEqual(Queue.objects.filter(name='new_queue').count(), 1)
        self.assertEqual(str(Queue.objects.filter(name='new_queue')[0].team.id),
                         str(Team.objects.filter(name="Admin")[0].id))

