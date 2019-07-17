from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from users.models import ExporterUser


class UserTests(DataTestClient):

    def test_user_creates_new_user(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jsmith@name.com',
            'password': 'password123'
        }
        url = reverse('users:users')
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExporterUser.objects.filter(organisation=self.test_helper.organisation).count(), 2)

    def test_fail_create_new_user(self):
        data = {}
        url = reverse('users:users')
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExporterUser.objects.filter(organisation=self.test_helper.organisation).count(), 1)
