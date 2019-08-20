from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class ExporterUserAuthenticateTests(DataTestClient):

    url = reverse('users:authenticate')

    def test_authentication_success(self):
        """
        Authorises user then checks the token which is sent is valid upon another request
        """
        data = {
            'email': self.exporter_user.email
        }

        response = self.client.post(self.url, data)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # headers = {'HTTP_EXPORTER_USER_TOKEN': response_data['token']}

        # TODO: fix
        # url = reverse('users:users')
        #
        # response = self.client.get(url, **headers)
        #
        # self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty(self):
        data = {
            'email': None,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_incorrect_details(self):
        data = {
            'email': 'something@random.com',
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # @parameterized.expand([
    #     [{'headers': {}}],
    #     [{'headers': {'HTTP_EXPORTER_USER_EMAIL': str('sadkjaf@asdasdf.casdas')}}],
    # ])
    # def test_authorised_valid_email_in_header(self, data):
    #     url = reverse('users:users')
    #     headers = data['headers']
    #     response = self.client.get(url, **headers)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
