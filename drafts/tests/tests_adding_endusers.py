import json

from django.urls import reverse
from rest_framework import status

from drafts.models import Draft
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class EndUserOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.primary_site = self.org.primary_site
        self.draft = OrgAndUserHelper.complete_draft('Goods test', self.org)
        self.end_user = OrgAndUserHelper.create_end_user('test', self.org)

        self.url = reverse('drafts:end_users', kwargs={'pk': self.draft.id})

    def test_add_end_user_to_a_draft(self):
        data = {
            'endusers': [
                self.end_user.id
            ]
        }
        self.draft = Draft.objects.get(pk=self.draft.id)

        response = self.client.post(self.url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('drafts:end_users', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.headers).json()
        self.assertEqual(len(response["end_users"]), 1)

    def test_multiple_end_users_to_a_draft(self):
        end_user_2 = OrgAndUserHelper.create_end_user('test_2', self.org)
        data = {
            'endusers': [
                self.end_user.id,
                end_user_2.id
            ]
        }
        self.draft = Draft.objects.get(pk=self.draft.id)

        response = self.client.post(self.url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('drafts:end_users', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.headers).json()
        self.assertEqual(len(response["end_users"]), 2)

    def test_user_cannot_add_another_organisations_site_to_a_draft(self):
        org2 = OrgAndUserHelper(name='organisation2').organisation
        test_end_user = OrgAndUserHelper.create_end_user('test', org2)

        data = {
            'endusers': [
                test_end_user.id
            ]
        }

        url = reverse('drafts:end_users', kwargs={'pk': self.draft.id})
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse('drafts:end_users', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["end_users"]), 0)
    #
    # def test_add_a_site_to_a_draft_deletes_existing_sites(self):
    #     site2, address = OrgAndUserHelper.create_site('site2', self.org)
    #
    #     # Add an initial site to the draft
    #     existing_site_on_draft = SitesOnDraft(site=site2, draft=self.draft)
    #     existing_site_on_draft.save()
    #
    #     # Ensure it's there
    #     url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
    #     response = self.client.get(url, **self.headers).json()
    #     site_id = response["sites"][0]['id']
    #     self.assertEqual(len(response["sites"]), 1)
    #
    #     # Post a new site to the draft, with the expectation that the existing site is deleted
    #     data = {
    #         'sites': [
    #             self.primary_site.id
    #         ]
    #     }
    #
    #     url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
    #     response = self.client.post(url, data, format='json', **self.headers)
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #
    #     # Check that the new site has been added, and the old one deleted
    #     url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})
    #     response = self.client.get(url, **self.headers).json()
    #     self.assertEqual(len(response['sites']), 1)
    #     self.assertNotEqual(response['sites'][0]['id'], site_id)
