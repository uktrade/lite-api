from django.urls import reverse
from rest_framework import status

from picklists.enums import PicklistType, PickListStatus
from test_helpers.clients import DataTestClient


class PicklistItemCreate(DataTestClient):

    url = reverse('picklist_items:picklist_items')

    def test_gov_user_can_add_item_to_picklist(self):
        data = {
            'name': 'picklist entry name',
            'text': 'ats us nai',
            'type': PicklistType.ECJU,
            'team': str(self.team.id),
            'status': PickListStatus.ACTIVE,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['picklist_item']['name'], data['name'])
        self.assertEqual(response_data['picklist_item']['text'], data['text'])
        self.assertEqual(response_data['picklist_item']['type']['key'], data['type'])
        self.assertEqual(response_data['picklist_item']['team'], data['team'])
        self.assertEqual(response_data['picklist_item']['status']['key'], data['status'])
