import json

from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from test_helpers.org_and_user_helper import OrgAndUserHelper


class SitesOnDraftTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_add_a_site_to_a_draft(self):
        org = self.test_helper.organisation
        draft = OrgAndUserHelper.complete_draft('Goods test', org)
        site, address = OrgAndUserHelper.create_site('site2', org)

        data = {
            'sites': [site.id],
        }

        url = reverse('drafts:draft_sites', kwargs={'pk': draft.id})
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('drafts:draft_sites', kwargs={'pk': draft.id})
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["sites"]), 1)

    def test_multiple_sites_to_a_draft(self):
        org = self.test_helper.organisation
        primary_site = org.primary_site
        draft = OrgAndUserHelper.complete_draft('Goods test', org)
        site2, address = OrgAndUserHelper.create_site('site2', org)

        data = {
            'sites': [primary_site.id, site2.id]
        }

        url = reverse('drafts:draft_sites', kwargs={'pk': draft.id})
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('drafts:draft_sites', kwargs={'pk': draft.id})
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["sites"]), 2)
