import json

from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from django.urls import path, include, reverse
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import User


class UserTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('users/', include('users.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_deactivate_a_user(self):
        user = OrgAndUserHelper.create_additional_users(self.test_helper.organisation)
        data = {
            'status': 'deactivated'
        }
        url = reverse('users:user', kwargs={'pk': user.id})
        response = self.client.put(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_deactivate_and_reactivate_a_user(self):
        user = OrgAndUserHelper.create_additional_users(self.test_helper.organisation)
        url = reverse('users:authenticate')
        data = {
            'email': user.email,
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = {
            'status': 'deactivated'
        }
        url = reverse('users:user', kwargs={'pk': user.id})
        self.client.put(url, data, format='json', **self.headers)
        data = {
            'status': 'active'
        }
        self.client.put(url, data, format='json', **self.headers)
        url = reverse('users:authenticate')
        data = {
            'email': user.email,
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
