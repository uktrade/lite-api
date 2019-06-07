from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

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

    def test_user_creates_new_user(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jsmith@name.com',
            'password': 'password123'
        }
        url = reverse('users:users')
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(organisation=self.test_helper.organisation).count(), 2)

    def test_fail_create_new_user(self):
        data = {}
        url = reverse('users:users')
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(organisation=self.test_helper.organisation).count(), 1)
