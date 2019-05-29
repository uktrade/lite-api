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
        self.external_site = self.test_helper.create_external_site('storage facility', self.org)
        self.draft = OrgAndUserHelper.complete_draft('Goods test', self.org)

        self.url = reverse('drafts:draft_external_sites', kwargs={'pk': self.draft.id})

    def test_add_external_site_to_a_draft(self):
        data = {
            'external_sites': [
                self.external_site.id
            ]
        }

        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.draft = Draft.objects.get(pk=self.draft.id)
        self.assertEqual(self.draft.activity, 'Brokering')

        url = reverse('drafts:draft_external_sites', kwargs={'pk': self.draft.id})
        response = self.client.get(url, **self.headers).json()
        self.assertEqual(len(response["external_sites"]), 1)