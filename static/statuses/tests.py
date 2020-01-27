from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class StatusesTests(DataTestClient):

    url = reverse("static:statuses:case_statuses")

    def test_get_statuses(self):
        response = self.client.get(self.url)
        data = response.json()["statuses"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", data[0])
        self.assertEqual(data[0]["priority"], 1)
        self.assertEqual(data[0]["key"], "submitted")
        self.assertEqual(data[0]["value"], "Submitted")
