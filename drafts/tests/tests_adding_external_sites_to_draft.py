from django.urls import reverse
from rest_framework import status

from drafts.models import SiteOnDraft, Draft, ExternalLocationOnDraft
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ExternalLocationsOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.external_location = self.create_external_location('storage facility', self.exporter_user.organisation)
        self.draft = self.create_standard_draft(self.exporter_user.organisation)

        self.url = reverse('drafts:draft_external_locations', kwargs={'pk': self.draft.id})

    def test_add_external_location_to_a_draft(self):
        data = {
            'external_locations': [
                self.external_location.id
            ]
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.draft = Draft.objects.get(pk=self.draft.id)
        self.assertEqual(self.draft.activity, 'Brokering')

        url = reverse('drafts:draft_external_locations', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.exporter_headers).json()
        self.assertEqual(len(response["external_locations"]), 1)

    def test_adding_external_location_to_draft_removes_sites(self):
        url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
        data = {
            'sites': [
                self.test_helper.primary_site.id
            ]
        }
        self.client.post(url, data, **self.exporter_headers)
        data = {
            'external_locations': [
                self.external_location.id
            ]
        }
        self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(SiteOnDraft.objects.filter(draft=self.draft).count(), 0)
        self.assertEqual(ExternalLocationOnDraft.objects.filter(draft=self.draft).count(), 1)
