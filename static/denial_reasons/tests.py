from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import BaseTestClient


class DenialReasonsTests(BaseTestClient):

    url = reverse('static:denial_reasons:denial_reasons')

    def test_get_denial_reasons(self):
        response = self.client.get(self.url)
        denial_reasons = response.json()['denial_reasons']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(len(denial_reasons), 0)
