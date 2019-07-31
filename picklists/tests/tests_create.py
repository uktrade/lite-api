import json
from django.urls import reverse
from rest_framework import status
from picklists.enums import PicklistType, PickListStatus
from test_helpers.clients import DataTestClient


class PickLists(DataTestClient):

    url = reverse('picklist_items:picklist_items')

    def test_gov_user_can_add_item_to_picklist(self):
        data = {
            'name': 'picklist entry name',
            'text': 'ats us nai',
            'type': PicklistType.ECJU,
            'team': self.team.id,
            'status': PickListStatus.ACTIVATE,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data['picklist_item']['name'], data['name'])

