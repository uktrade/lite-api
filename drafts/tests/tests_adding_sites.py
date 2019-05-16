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
        # good = OrgAndUserHelper.create_controlled_good('A good', org)
        site, address = OrgAndUserHelper.create_site('site2', org)

        data = {
            'draft_id': draft.id,
            'site_id': site.id,
        }

        url = reverse('drafts:draft_sites', kwargs={'pk': draft.id})
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
