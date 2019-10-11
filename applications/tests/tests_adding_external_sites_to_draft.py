from django.urls import reverse
from rest_framework import status

from applications.models import StandardApplication, SiteOnApplication, ExternalLocationOnApplication
from test_helpers.clients import DataTestClient


class ExternalLocationsOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.external_location = self.create_external_location('storage facility', self.organisation)
        self.draft = self.create_standard_draft(self.organisation)

        self.url = reverse('applications:application_external_locations', kwargs={'pk': self.draft.id})

    def test_add_external_location_to_a_draft(self):
        data = {
            'external_locations': [
                self.external_location.id
            ]
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.draft = StandardApplication.objects.get(pk=self.draft.id)
        self.assertEqual(self.draft.activity, 'Brokering')

        url = reverse('applications:application_external_locations', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.exporter_headers).json()
        self.assertEqual(len(response["external_locations"]), 1)

    def test_adding_external_location_to_draft_removes_sites(self):
        url = reverse('applications:application_sites', kwargs={'pk': self.draft.id})
        data = {
            'sites': [
                self.organisation.primary_site.id
            ]
        }
        self.client.post(url, data, **self.exporter_headers)
        data = {
            'external_locations': [
                self.external_location.id
            ]
        }
        self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(SiteOnApplication.objects.filter(application=self.draft).count(), 0)
        self.assertEqual(ExternalLocationOnApplication.objects.filter(application=self.draft).count(), 1)
