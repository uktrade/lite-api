import json

from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from organisations.models import ExternalLocation
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ExternalLocationViewTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='Org1')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}
        self.external_location = OrgAndUserHelper.create_external_location(name='storage facility',
                                                                   org=self.test_helper.organisation)

    def test_site_list(self):
        url = reverse('organisations:external_locations')
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['external_locations'][0]['name'], 'storage facility')

    def test_create_external_location(self):
        url = reverse('organisations:external_locations')
        data = {'name': 'regional site',
                'address': 'A location',
                'country': 'GB'}

        response = self.client.post(url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExternalLocation.objects.all().count(), 2)

    def test_add_external_location_via_helper(self):
        external_location = OrgAndUserHelper.create_external_location('org2', self.test_helper.organisation)
        self.assertEqual(ExternalLocation.objects.all().count(), 2)
        self.assertEqual(ExternalLocation.objects.filter(id=external_location.id).count(), 1)

    def test_failed_create_external_location(self):
        data = {'name': '',
                'address': '',
                'country': ''}
        url = reverse('organisations:external_locations')
        response = self.client.post(url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExternalLocation.objects.all().count(), 1)
