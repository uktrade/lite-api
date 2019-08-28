from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class UserTests(DataTestClient):

    def test_user_can_view_their_own_profile_info(self):
        """
        Tests the 'users/me' endpoint
        Ensures that the endpoint returns the correct details about the signed in user
        """
        url = reverse('users:me')

        response, status_code = self.get(url, **self.exporter_headers)

        self.assertEqual(status_code, status.HTTP_200_OK)

        self.assertEqual(response['user']['id'], str(self.exporter_user.id))
        self.assertEqual(response['user']['first_name'], self.exporter_user.first_name)
        self.assertEqual(response['user']['last_name'], self.exporter_user.last_name)
