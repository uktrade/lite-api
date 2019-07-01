import json

from parameterized import parameterized
from django.urls import reverse
from rest_framework import status

from static.units.enums import Units
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class DraftTests(DataTestClient):

    def test_add_a_good_to_a_draft(self):
        org = self.test_helper.organisation
        draft = OrgAndUserHelper.complete_draft('Goods test', org)
        good = OrgAndUserHelper.create_controlled_good('A good', org)

        data = {
            'good_id': good.id,
            'quantity': 1200.098896,
            'unit': Units.NAR,
            'value': 50000.45
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
            'unit': Units.KGM,
            'value': 50000
        }

        url = reverse('drafts:draft_goods', kwargs={'pk': draft.id})
        response = self.client.post(url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('drafts:draft_goods', kwargs={'pk': draft.id})
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["goods"]), 0)

    @parameterized.expand([
        [{'value': '123.45', 'quantity': '1123423.901234', 'response': status.HTTP_201_CREATED}],
        [{'value': '123.45', 'quantity': '1234.12341341', 'response': status.HTTP_400_BAD_REQUEST}],
        [{'value': '2123.45', 'quantity': '1234', 'response': status.HTTP_201_CREATED}],
        [{'value': '123.4523', 'quantity': '1234', 'response': status.HTTP_400_BAD_REQUEST}],
    ])
    def test_adding_goods_with_different_number_formats(self, data):
        org = self.test_helper.organisation
        draft = OrgAndUserHelper.complete_draft('Goods test', org)
        good = OrgAndUserHelper.create_controlled_good('A good', org)

        post_data = {
            'good_id': good.id,
            'quantity': data['quantity'],
            'unit': Units.NAR,
            'value': data['value']
        }

        url = reverse('drafts:draft_goods', kwargs={'pk': draft.id})
        response = self.client.post(url, post_data, **self.headers)
        self.assertEqual(response.status_code, data['response'])
