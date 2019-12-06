from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class ExporterUserAuthenticateTests(DataTestClient):

    url = reverse("users:authenticate")

    def test_authentication_success(self):
        """
        Authorises user then checks the token which is sent is valid upon another request
        """
        data = {"email": self.exporter_user.email, "user_profile": {"first_name": "Matt", "last_name": "Berninger"}}

        response = self.client.post(self.url, data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            "HTTP_EXPORTER_USER_TOKEN": response_data["token"],
            "HTTP_ORGANISATION_ID": str(self.organisation.id),
        }

        response = self.client.get(reverse("goods:goods"), **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_authenticate_user_with_empty_data(self):
        data = {"email": None, "user_profile": {"first_name": None, "last_name": None}}

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_authenticate_user_with_incorrect_details(self):
        data = {"email": "something@random.com", "user_profile": {"first_name": "Bob", "last_name": "Dell"}}

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
