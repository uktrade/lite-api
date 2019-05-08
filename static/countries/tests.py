import json

from django.urls import include, path
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase


class CountriesTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('static/countries', include('static.countries.urls')),
    ]
    client = APIClient

    def test_get_countries(self):
        url = reverse('countries:countries')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['countries'][0]['name'], 'Abu Dhabi')
