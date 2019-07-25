import json
from django.urls import reverse
from rest_framework import status
from picklist_items.enums import PicklistType
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class PickLists(DataTestClient):

    def test_deactivate_a_picklist_item(self):
        picklist_item = OrgAndUserHelper.create_picklist_item(PicklistType.ACTIVATE, self.team)

        data = {
            'status': PicklistType.DEACTIVATE
        }

        url = reverse('picklist_items:picklist_item', kwargs={'pk': picklist_item.id})
        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(picklist_item.status, PicklistType.DEACTIVATE)

    def test_reactivate_a_picklist_item(self):
        picklist_item = OrgAndUserHelper.create_picklist_item(PicklistType.DEACTIVATE, self.team)

        data = {
            'status': PicklistType.ACTIVATE
        }

        url = reverse('picklist_items:picklist_item', kwargs={'pk': picklist_item.id})
        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(picklist_item.status, PicklistType.ACTIVATE)