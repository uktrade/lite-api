import json

from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from test_helpers.org_and_user_helper import OrgAndUserHelper

from static.quantity.units import Units

class DraftTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_add_a_good_to_a_draft(self):
        org = self.test_helper.organisation
        draft = OrgAndUserHelper.complete_draft('Goods test', org)
        good = OrgAndUserHelper.create_controlled_good('A good', org)

        data = {
            'good_id': good.id,
            'quantity': 1200,
            'unit': 'NAR',
            'value': 50000
        }

        url = reverse('drafts:draft_goods', kwargs={'pk': draft.id})
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = '/drafts/' + str(draft.id) + '/goods/'
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["goods"]), 1)

    def test_user_cannot_add_another_organisations_good_to_a_draft(self):
        test_helper_2 = OrgAndUserHelper(name='organisation2')
        good = OrgAndUserHelper.create_controlled_good('test', test_helper_2.organisation)
        draft = OrgAndUserHelper.complete_draft('test', self.test_helper.organisation)

        data = {
            'draft': draft.id,
            'good_id': good.id,
            'quantity': 1200,
            'unit': 'kg',
            'value': 50000
        }

        url = reverse('drafts:draft_goods', kwargs={'pk': draft.id})
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('drafts:draft_goods', kwargs={'pk': draft.id})
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["goods"]), 0)
