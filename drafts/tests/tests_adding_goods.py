import json

from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class DraftTests(DataTestClient):

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
        response = self.client.post(url, data, **self.headers)
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
        response = self.client.post(url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('drafts:draft_goods', kwargs={'pk': draft.id})
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["goods"]), 0)
