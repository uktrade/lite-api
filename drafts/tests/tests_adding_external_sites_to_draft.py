import json

from django.urls import reverse
from rest_framework import status

from drafts.models import SiteOnDraft, Draft
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ExternalSitesOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.primary_site = self.org.primary_site
        self.draft = OrgAndUserHelper.complete_draft('Goods test', self.org)

        self.url = reverse('drafts:draft_sites', kwargs={'pk': self.draft.id})

    def test_add_external_site_to_a_draft(self):
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