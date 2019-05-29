import json

from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from addresses.models import Address
from organisations.models import Site, ExternalSite
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ExternalSiteViewTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='Org1')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}
        self.external_site = OrgAndUserHelper.create_external_site(name='storage facility',
                                                                   org=self.test_helper.organisation)

    def test_site_list(self):
        url = reverse('organisations:external_sites')
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['external_sites'][0]['name'], 'storage facility')

    def test_create_external_site(self):
        url = reverse('organisations:external_sites')
        data = {'name': 'regional site',
                'address': 'A location',
                'country': 'England'}

        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExternalSite.objects.all().count(), 2)

    def test_add_external_site_via_helper(self):
        OrgAndUserHelper.create_external_site('org2', self.test_helper.organisation)
        self.assertEqual(ExternalSite.objects.all().count(), 2)

    def test_failed_create_external_site(self):
        data = {'name': '',
                'address': '',
                'country': ''}
        url = reverse('organisations:external_sites')
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExternalSite.objects.all().count(), 1)
