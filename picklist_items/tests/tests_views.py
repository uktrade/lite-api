import json
from django.urls import reverse
from rest_framework import status
from picklist_items.enums import PicklistType, PickListStatus
from test_helpers.clients import DataTestClient
from picklist_items.models import PicklistItem
from test_helpers.org_and_user_helper import OrgAndUserHelper


class PickLists(DataTestClient):

    def test_gov_user_can_get_picklist_items(self):
        picklist_item = PicklistItem(team=self.team,
                                     name='Picklist Item 1',
                                     text='This is a string of text, do not disturb the milk argument',
                                     type=PicklistType.ECJU,
                                     status=PickListStatus.ACTIVATE)

        picklist_item.save()
        url = reverse('picklist_items:picklist_items')
        response = self.client.get(url, **{'HTTP_USER_ID': str(self.test_helper.user.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_picklist_items_query_filter_by_type(self):
        OrgAndUserHelper.create_picklist_item(PickListStatus.ACTIVATE, self.team, PicklistType.ANNUAL_REPORT_SUMMARY)
        OrgAndUserHelper.create_picklist_item(PickListStatus.ACTIVATE, self.team, PicklistType.ANNUAL_REPORT_SUMMARY)
        OrgAndUserHelper.create_picklist_item(PickListStatus.ACTIVATE, self.team)

        url = reverse('picklist_items:picklist_items') + '?type=' + PicklistType.ANNUAL_REPORT_SUMMARY
        response = self.client.get(url, **{'HTTP_USER_ID': str(self.test_helper.user.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)["picklist_items"]
        self.assertEqual(len(response_data), 2)
