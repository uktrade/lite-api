from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class ViewQueuesTests(DataTestClient):

    url = reverse('queues:queues')

    def test_whitelisted_gov_user_can_see_queues(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
