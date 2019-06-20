from django.urls import reverse
from rest_framework import status

from queues.models import Queue
from teams.models import Team
from test_helpers.clients import DataTestClient


class QueueCreateTests(DataTestClient):

    url = reverse('queues:queues')

    def tests_create_queue(self):
        existing_queues_count = Queue.objects.all().count()
        team = Team.objects.get()

        data = {
            'name': 'new_queue',
            'team': team.id,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        queue_json = response.json().get('queue')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Queue.objects.all().count(), existing_queues_count + 1)
        self.assertEqual(queue_json.get('name'), data['name'])
        self.assertEqual(queue_json.get('team'), str(team.id))

