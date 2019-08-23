from rest_framework import status
from rest_framework.reverse import reverse

from organisations.models import ExternalLocation
from test_helpers.clients import DataTestClient


class OrganisationExternalLocationsTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.external_location = self.create_external_location(name='storage facility',
                                                               org=self.organisation)
        self.url = reverse('organisations:external_locations', kwargs={'org_pk': self.organisation.pk})

    def test_site_list(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['external_locations'][0]['name'], self.external_location.name)

    def test_create_external_location(self):
        data = {
            'name': 'regional site',
            'address': 'A location',
            'country': 'GB'
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExternalLocation.objects.all().count(), 2)

    def test_failed_create_external_location(self):
        data = {
            'name': '',
            'address': '',
            'country': ''
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExternalLocation.objects.all().count(), 1)
