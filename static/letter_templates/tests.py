from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class LetterTemplatesTests(DataTestClient):

    url = reverse('static:letter_templates:letter_templates')

    def test_get_countries(self):
        response = self.client.get(self.url)
        response_data = response.json()['letter_templates']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
