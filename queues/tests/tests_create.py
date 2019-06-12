from django.urls import reverse
from rest_framework import status

from queues.models import Queue
from teams.models import Team
from test_helpers.clients import DataTestClient


class QueueCreateTests(DataTestClient):

    url = reverse('queues:queues')

    def tests_create_queue(self):
        data = {
            'name': 'new_queue',
            'team': str(Team.objects.filter(name="Reception")[0].id),
            'cases': {}
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Note: A queue "New Cases" is created by default
        self.assertEqual(Queue.objects.all().count(), 2)
        self.assertEqual(Queue.objects.filter(name='new_queue').count(), 1)
        all_queue_records = Queue.objects.all()
        queue_record = Queue.objects.filter(name='new_queue')[0]
        self.assertEqual(str(Queue.objects.filter(name='new_queue')[0].team.id),
                         str(Team.objects.filter(name="Reception")[0].id))
