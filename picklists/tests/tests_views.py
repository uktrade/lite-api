from django.test import tag
from django.urls import reverse
from rest_framework import status

from picklists.enums import PicklistType, PickListStatus
from test_helpers.clients import DataTestClient


class PicklistsViews(DataTestClient):

    url = reverse('picklist_items:picklist_items')

    def setUp(self):
        super().setUp()
        other_team = self.create_team('Team')
        self.create_picklist_item('#2', self.team, PicklistType.REPORT_SUMMARY, PickListStatus.ACTIVE)
        self.create_picklist_item('#3', self.team, PicklistType.REPORT_SUMMARY, PickListStatus.DEACTIVATED)
        self.picklist_item_1 = self.create_picklist_item('#1', self.team, PicklistType.PROVISO, PickListStatus.ACTIVE)
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

    def test_gov_user_can_see_filtered_picklist_items(self):
        response = self.client.get(self.url + '?type=' + PicklistType.REPORT_SUMMARY + '?show_deactivated=True', **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['picklist_items']), 1)

    def test_gov_user_can_see_filtered_picklist_items_excluding_deactivated(self):
        response = self.client.get(self.url + '?type=' + PicklistType.REPORT_SUMMARY, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['picklist_items']), 1)

    def test_gov_user_can_see_items_by_ids_filter(self):
        response = self.client.get(self.url + '?type=' + PicklistType.PROVISO + '&ids=' + str(self.picklist_item_1.id), **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['picklist_items']), 1)
