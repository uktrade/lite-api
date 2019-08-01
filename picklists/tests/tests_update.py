from rest_framework import status
from rest_framework.reverse import reverse

from picklists.enums import PickListStatus
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class PickListUpdate(DataTestClient):

    def setUp(self):
        super().setUp()
        self.picklist_item = OrgAndUserHelper.create_picklist_item(PickListStatus.ACTIVATE, self.team)
        self.url = reverse('picklist_items:picklist_item', kwargs={'pk': self.picklist_item.id})

    def test_deactivate_a_picklist_item(self):
        data = {
            'status': PickListStatus.DEACTIVATE
        }

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['picklist_item']['status'], PickListStatus.DEACTIVATE)
        self.assertEqual(response_data['picklist_item']['status'], {'key': PickListStatus.DEACTIVATE,
                                                                    'value': PickListStatus.DEACTIVATE})

    def test_reactivate_a_picklist_item(self):
        data = {
            'status': PickListStatus.ACTIVATE
        }

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['picklist_item']['status'], PickListStatus.ACTIVATE)
        self.assertEqual(response_data['picklist_item']['status'], {'key': PickListStatus.ACTIVATE,
                                                                    'value': PickListStatus.ACTIVATE})