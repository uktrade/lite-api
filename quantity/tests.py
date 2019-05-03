import json

from django.urls import path, include
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from test_helpers.org_and_user_helper import OrgAndUserHelper


class QuantityUnitsTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('quantity/', include('quantity.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_get_units(self):
        url = reverse('quantity:quantity')
        response = self.client.get(url, **self.headers)
        # response = self.client.get(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        print(response_data)

