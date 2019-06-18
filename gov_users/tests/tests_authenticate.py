from django.urls import path, include, reverse
from parameterized import parameterized
from rest_framework import status
from rest_framework.utils import json

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
        self.url = reverse('gov_users:authenticate')

    def test_authentication_success(self):
        """
        Authorises user then checks the token which is sent is valid upon another request
        """
        data = {
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        headers = {'HTTP_GOV_USER_TOKEN': response_data['token']}
        url = reverse('gov_users:gov_users')
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty(self):
        data = {
            'email': None,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_incorrect_details(self):
        data = {
            'email': 'something@random.com',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_a_deactivated_user_cannot_log_in(self):
        self.user.status = GovUserStatuses.DEACTIVATED
        self.user.save()
        data = {
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @parameterized.expand([
        [{'headers': {'HTTP_GOV_USER_EMAIL': str('test@mail.com')}, 'response': status.HTTP_200_OK}],
        [{'headers': {'HTTP_GOV_USER_TOKEN': str('43a88949-5db9-4334-b0cc-044e91827451')}, 'response': status.HTTP_200_OK}],
        [{'headers': {}, 'response': status.HTTP_403_FORBIDDEN}],
        [{'headers': {'HTTP_GOV_USER_EMAIL': str('sadkjaf@asdasdf.casdas')}, 'response': status.HTTP_403_FORBIDDEN}],
    ])
    def test_authorised_valid_email_in_header(self, data):
        url = reverse('gov_users:gov_users')
        headers = data['headers']
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, data['response'])
