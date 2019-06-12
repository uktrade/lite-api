from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class QueueListAndDetailTests(DataTestClient):

    def setUp(self):
        super().setUp()

    def test_non_whitelisted_gov_user_cannot_see_the_queues(self):
        url = reverse('queues:queues')
        headers = {'HTTP_GOV_USER_EMAIL': str('test2@mail.com')}
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_whitelisted_gov_user_can_see_queues(self):
        url = reverse('queues:queues')
        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)