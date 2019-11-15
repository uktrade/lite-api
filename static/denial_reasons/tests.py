from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class DenialReasonsTests(DataTestClient):

    url = reverse("static:denial-reasons:denial-reasons")

    def test_get_denial_reasons(self):
        response = self.client.get(self.url)
        denial_reasons = response.json()["denial_reasons"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(len(denial_reasons), 0)
