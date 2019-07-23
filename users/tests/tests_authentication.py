from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import UserStatuses


class UserTests(DataTestClient):

    def test_login_success(self):
        url = reverse('users:authenticate')
        data = {
            'email': self.test_helper.user.email,
            'password': self.test_helper.password
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_empty(self):
        url = reverse('users:authenticate')
        data = {
            'email': None,
            'password': None
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_login_incorrect_details(self):
        url = reverse('users:authenticate')
        data = {
            'email': self.test_helper.user.email,
            'password': 'This is not the password'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_deactivated_user_cannot_log_in(self):
        user = OrgAndUserHelper.create_additional_users(self.test_helper.organisation)

        data = {
            'email': user.email,
            'password': 'password'
        }
        user.status = UserStatuses.DEACTIVATED
        user.save()
        url = reverse('users:authenticate')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
