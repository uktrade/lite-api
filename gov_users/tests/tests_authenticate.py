from django.urls import path, include, reverse
from rest_framework import status

from gov_users.enums import GovUserStatuses
from gov_users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient


class GovUserAuthenticateTests(DataTestClient):

    urlpatterns = [
        path('gov-users/', include('gov_users.urls')),
        path('organisations', include('organisations.urls'))
    ]

    def setUp(self):
        super().setUp()

    def test_authentication_success(self):
        url = reverse('gov_users:authenticate')
        data = {
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty(self):
        url = reverse('gov_users:authenticate')
        data = {
            'email': None,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_incorrect_details(self):
        url = reverse('gov_users:authenticate')
        data = {
            'email': 'something@random.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_a_deactivated_user_cannot_log_in(self):
        self.user.status = GovUserStatuses.DEACTIVATED
        self.user.save()
        data = {
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        }
        url = reverse('gov_users:authenticate')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_with_email_in_header(self):
        url = reverse('gov_users:gov_users')
        headers = {'HTTP_GOV_USER_EMAIL': str(self.user.email)}
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_with_token_in_header(self):
        url = reverse('gov_users:gov_users')
        headers = {'HTTP_GOV_USER_TOKEN': str(user_to_token(self.user))}
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)