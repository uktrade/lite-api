from django.urls import reverse
from rest_framework import status
from picklist_items.enums import PicklistType, PickListStatus
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class PickLists(DataTestClient):

    url = reverse('picklist_items:picklist_items')

    def test_gov_user_can_see_all_picklist_items(self):

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_whitelisted_gov_user_cannot_see_the_picklist_items(self):
        headers = {'HTTP_GOV_USER_EMAIL': str('test2@mail.com')}
        response = self.client.get(self.url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_gov_user_can_see_filtered_picklist_items(self):
        other_team = self.create_team("Team")

        OrgAndUserHelper.create_picklist_item(PickListStatus.ACTIVATE, self.team, PicklistType.ANNUAL_REPORT_SUMMARY)
        OrgAndUserHelper.create_picklist_item(PickListStatus.ACTIVATE, self.team, PicklistType.ANNUAL_REPORT_SUMMARY)
        OrgAndUserHelper.create_picklist_item(PickListStatus.ACTIVATE, other_team)

        response = self.client.get(self.url + '?type=' + PicklistType.ANNUAL_REPORT_SUMMARY + '&team=' + self.team.name, **self.gov_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['picklist_items']), 2)

    def test_gov_user_can_see_no_picklist_items_when_team_doesnt_exist(self):
        response = self.client.get(self.url + '?type=' + PicklistType.ANNUAL_REPORT_SUMMARY + '&team=blah', **self.gov_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['picklist_items']), 0)