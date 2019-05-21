import json

from django.urls import reverse
from rest_framework import status

from drafts.models import SiteOnDraft, Draft
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class SitesOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.primary_site = self.org.primary_site
        self.draft = OrgAndUserHelper.complete_draft('Goods test', self.org)

        self.url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})

    def test_add_site_to_a_draft(self):
        data = {
            'sites': [
                self.primary_site.id
            ]
        }

        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.draft = Draft.objects.get(pk=self.draft.id)
        self.assertEqual(self.draft.activity, 'Trading')

        url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.headers).json()
        self.assertEqual(len(response["sites"]), 1)

    def test_add_multiple_sites_to_a_draft(self):
        site2, address = OrgAndUserHelper.create_site('site2', self.org)

        data = {
            'sites': [
                self.primary_site.id,
                site2.id
            ]
        }

        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.draft = Draft.objects.get(pk=self.draft.id)
        self.assertEqual(self.draft.activity, 'Trading')

        url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["sites"]), 2)

    def test_user_cannot_add_another_organisations_site_to_a_draft(self):
        org2 = OrgAndUserHelper(name='organisation2')
        site_org2 = org2.primary_site

        data = {
            'sites': [
                site_org2.id
            ]
        }

        url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
        response = self.client.post(url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["sites"]), 0)

    def test_add_a_site_to_a_draft_deletes_existing_sites(self):
        site2, address = OrgAndUserHelper.create_site('site2', self.org)

        # Add an initial site to the draft
        existing_site_on_draft = SiteOnDraft(site=site2, draft=self.draft)
        existing_site_on_draft.save()

        # Ensure it's there
        url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.headers).json()
        site_id = response["sites"][0]['id']
        self.assertEqual(len(response["sites"]), 1)

        # Post a new site to the draft, with the expectation that the existing site is deleted
        data = {
            'sites': [
                self.primary_site.id
            ]
        }

        url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
        response = self.client.post(url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that the new site has been added, and the old one deleted
        url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.headers).json()
        self.assertEqual(len(response['sites']), 1)
        self.assertNotEqual(response['sites'][0]['id'], site_id)
