import json

from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import ExporterUser


class UserTests(DataTestClient):

    def test_edit_a_user(self):
        user = OrgAndUserHelper.create_additional_users(self.test_helper.organisation, 1)
        original_first_name = user.first_name
        original_last_name = user.last_name
        original_email = user.email
        original_password = user.password

        data = {
            'first_name': 'hamster',
            'last_name': 'gerbal',
            'email': 'some@thing.com',
            'password': '1234'
        }

        url = reverse('users:user', kwargs={'pk': user.id})
        response = self.client.put(url, data, **self.exporter_headers)
        response_data = json.loads(response.content)

        self.assertNotEqual(response_data['user']['first_name'], original_first_name)
        self.assertNotEqual(response_data['user']['last_name'], original_last_name)
        self.assertNotEqual(response_data['user']['email'], original_email)
        self.assertNotEqual(ExporterUser.objects.get(email='some@thing.com').password, original_password)

        # Show that new password works with login
        url = reverse('users:authenticate')
        data = {
            'email': 'some@thing.com',
            'password': '1234'
        }
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_edit_a_user_some_fields(self):
        user = OrgAndUserHelper.create_additional_users(self.test_helper.organisation, 1)
        original_first_name = user.first_name
        original_last_name = user.last_name
        original_email = user.email
        original_password = user.password

        data = {
            'first_name': 'hamster',
            'last_name': 'gerbal'
        }

        url = reverse('users:user', kwargs={'pk': user.id})
        response = self.client.put(url, data, **self.exporter_headers)
        response_data = json.loads(response.content)

        self.assertNotEqual(response_data['user']['first_name'], original_first_name)
        self.assertNotEqual(response_data['user']['last_name'], original_last_name)
        self.assertEqual(response_data['user']['email'], original_email)
        self.assertEqual(ExporterUser.objects.get(email=user.email).password, original_password)
