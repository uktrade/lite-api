import json
from django.urls import reverse
from rest_framework import status
from picklists.enums import PickListStatus
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class PickLists(DataTestClient):

    def test_deactivate_a_picklist_item(self):
        picklist_item = OrgAndUserHelper.create_picklist_item(PickListStatus.ACTIVATE, self.team)

        data = {
            'status': PickListStatus.DEACTIVATE
        }

        url = reverse('picklist_items:picklist_item', kwargs={'pk': picklist_item.id})
        response = self.client.put(url, data, **self.gov_headers)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['picklist_item']['status'], PickListStatus.DEACTIVATE)

    def test_reactivate_a_picklist_item(self):
        picklist_item = OrgAndUserHelper.create_picklist_item(PickListStatus.DEACTIVATE, self.team)

        data = {
            'status': PickListStatus.ACTIVATE
        }

        url = reverse('picklist_items:picklist_item', kwargs={'pk': picklist_item.id})
        response = self.client.put(url, data, **self.gov_headers)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['picklist_item']['status'], PickListStatus.ACTIVATE)