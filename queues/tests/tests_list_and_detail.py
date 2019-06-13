from django.urls import reverse
from rest_framework import status

from teams.models import Team
from test_helpers.clients import DataTestClient


class QueueEditTests(DataTestClient):

    url = reverse('queues:queues')

    def tests_list_queue(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['queues'][0]['id'],
                         '00000000-0000-0000-0000-000000000001')

        data = {
            'name': 'new_queue',
            'team': str(Team.objects.filter(name="Reception")[0].id),
            'cases': {}
        }
        response = self.client.post(self.url, data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['queues']), 2)

    def tests_detail_queue(self):
        id = '00000000-0000-0000-0000-000000000001'
        url = reverse('queues:queue', kwargs={'pk': id})

        response = self.client.get(url, kwargs={'pk': id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['queue']['name'], 'New Cases')
