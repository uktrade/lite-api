from django.urls import reverse
from rest_framework import status

from picklists.enums import PicklistType, PickListStatus
from test_helpers.clients import DataTestClient


class PicklistsViews(DataTestClient):

    url = reverse('picklist_items:picklist_items')

    def setUp(self):
        super().setUp()
        other_team = self.create_team('Team')
        self.create_picklist_item('#1', self.team, PicklistType.PROVISO, PickListStatus.ACTIVE)
        self.create_picklist_item('#2', self.team, PicklistType.ANNUAL_REPORT_SUMMARY, PickListStatus.ACTIVE)
        self.create_picklist_item('#3', self.team, PicklistType.ANNUAL_REPORT_SUMMARY, PickListStatus.DEACTIVATED)
        self.create_picklist_item('#4', other_team, PicklistType.ECJU, PickListStatus.ACTIVE)

    def test_gov_user_can_see_all_their_teams_picklist_items(self):
        response = self.client.get(self.url + '?show_deactivated=True', **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['picklist_items']), 3)

    def test_gov_user_can_see_all_their_teams_picklist_items_excluding_deactivated(self):
        response = self.client.get(self.url + '?show_deactivated=False', **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['picklist_items']), 2)

    # TODO
    # def test_non_whitelisted_gov_user_cannot_see_the_picklist_items(self):
    #     headers = {'HTTP_GOV_USER_EMAIL': str('test2@mail.com')}
    #     response = self.client.get(self.url, **headers)
    #
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gov_user_can_see_filtered_picklist_items(self):
        response = self.client.get(self.url + '?type=' + PicklistType.ANNUAL_REPORT_SUMMARY + '?show_deactivated=True', **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['picklist_items']), 1)

    def test_gov_user_can_see_filtered_picklist_items_excluding_deactivated(self):
        response = self.client.get(self.url + '?type=' + PicklistType.ANNUAL_REPORT_SUMMARY, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['picklist_items']), 1)
