from django.urls import reverse
from rest_framework import status

from api.conf.constants import GovPermissions
from picklists.enums import PicklistType, PickListStatus
from test_helpers.clients import DataTestClient


class PicklistsViews(DataTestClient):

    url = reverse("picklist_items:picklist_items")

    def setUp(self):
        super().setUp()
        other_team = self.create_team("Team")
        self.picklist_item_1 = self.create_picklist_item("#1", self.team, PicklistType.PROVISO, PickListStatus.ACTIVE)
        self.picklist_item_2 = self.create_picklist_item("#2", self.team, PicklistType.PROVISO, PickListStatus.ACTIVE)
        self.create_picklist_item("#3", self.team, PicklistType.REPORT_SUMMARY, PickListStatus.ACTIVE)
        self.create_picklist_item("#4", self.team, PicklistType.REPORT_SUMMARY, PickListStatus.DEACTIVATED)
        self.create_picklist_item("#5", other_team, PicklistType.ECJU, PickListStatus.ACTIVE)

    def test_gov_user_can_see_all_their_teams_picklist_items(self):
        response = self.client.get(self.url + "?show_deactivated=True", **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 4)

    def test_gov_user_can_see_all_their_teams_picklist_items_excluding_deactivated(self,):
        response = self.client.get(self.url + "?show_deactivated=False", **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 3)

    def test_gov_user_can_see_all_their_teams_picklist_items_filter_by_name(self,):
        response = self.client.get(self.url + "?name=3", **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 1)

    def test_gov_user_can_see_filtered_picklist_items(self):
        response = self.client.get(
            self.url + "?type=" + PicklistType.REPORT_SUMMARY + "?show_deactivated=True", **self.gov_headers
        )
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 1)

    def test_gov_user_can_see_filtered_picklist_items_excluding_deactivated(self):
        response = self.client.get(self.url + "?type=" + PicklistType.REPORT_SUMMARY, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 1)

    def test_gov_user_can_see_items_by_ids_filter(self):
        response = self.client.get(
            self.url
            + "?type="
            + PicklistType.PROVISO
            + "&ids="
            + str(self.picklist_item_1.id)
            + ","
            + str(self.picklist_item_2.id),
            **self.gov_headers,
        )
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 2)


class PicklistView(DataTestClient):
    def setUp(self):
        super().setUp()
        self.picklist = self.create_picklist_item("#1", self.team, PicklistType.PROVISO, PickListStatus.ACTIVE)
        self.url = reverse("picklist_items:picklist_item", kwargs={"pk": self.picklist.id})

    def test_gov_user_can_view_a_picklist_item(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_PICKLISTS.name])

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["picklist_item"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.picklist.id))
        self.assertEqual(response_data["name"], self.picklist.name)
        self.assertEqual(response_data["text"], self.picklist.text)
        self.assertEqual(response_data["team"]["id"], str(self.team.id))
        self.assertEqual(response_data["team"]["name"], self.team.name)
        self.assertEqual(response_data["type"]["key"], self.picklist.type)
        self.assertEqual(response_data["status"]["key"], self.picklist.status)
