from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from test_helpers.helpers import create_additional_users
from users.models import ExporterUser


class UserTests(DataTestClient):

    def test_edit_a_user(self):
        original_first_name = self.exporter_user.first_name
        original_last_name = self.exporter_user.last_name
        original_email = self.exporter_user.email

        data = {
            'first_name': 'hamster',
            'last_name': 'gerbal',
            'email': 'some@thing.com',
        }

        url = reverse('users:user', kwargs={'pk': self.exporter_user.id})
        response = self.client.put(url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertNotEqual(response_data['user']['first_name'], original_first_name)
        self.assertNotEqual(response_data['user']['last_name'], original_last_name)
        self.assertNotEqual(response_data['user']['email'], original_email)

        url = reverse('users:authenticate')
        data = {
            'email': 'some@thing.com',
            'first_name': response_data['user']['first_name'],
            'last_name': response_data['user']['last_name']
        }
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_edit_a_user_some_fields(self):
        original_first_name = self.exporter_user.first_name
        original_last_name = self.exporter_user.last_name
        original_email = self.exporter_user.email

        data = {
            'first_name': 'hamster',
            'last_name': 'gerbal'
        }

        url = reverse('users:user', kwargs={'pk': self.exporter_user.id})

        response = self.client.put(url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertNotEqual(response_data['user']['first_name'], original_first_name)
        self.assertNotEqual(response_data['user']['last_name'], original_last_name)
        self.assertEqual(response_data['user']['email'], original_email)
