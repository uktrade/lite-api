import json
from django.urls import reverse
from rest_framework import status
from picklist_items.enums import PicklistType
from test_helpers.clients import DataTestClient
from parameterized import parameterized


class PickLists(DataTestClient):

    url = reverse('picklist_items:picklist_items')

    def test_gov_user_can_add_item_to_picklist(self):
        data = {
            'name': 'picklist entry name',
            'text': 'ats us nai',
            'type': PicklistType.ECJU,
            'team': self.team.id,
            'status': PicklistType.ACTIVATE,
        }
        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

