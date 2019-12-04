from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class UserTests(DataTestClient):
    def test_edit_a_user(self):
        data = {"email": "hamster@gmail.com"}
        url = reverse("users:user", kwargs={"pk": self.exporter_user.id})

        response = self.client.put(url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["user"]["email"], data["email"])
