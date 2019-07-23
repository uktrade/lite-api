import json

from rest_framework import status
from rest_framework.reverse import reverse

from organisations.models import ExternalLocation
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ExternalLocationViewTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.external_location = OrgAndUserHelper.create_external_location(name='storage facility',
                                                                           org=self.test_helper.organisation)

    def test_site_list(self):
        url = reverse('organisations:external_locations')
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['external_locations'][0]['name'], 'storage facility')

    def test_create_external_location(self):
        url = reverse('organisations:external_locations')
        data = {'name': 'regional site',
                'address': 'A location',
                'country': 'GB'}

        response = self.client.post(url, data, **self.exporter_headers)
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
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExternalLocation.objects.all().count(), 1)
