from rest_framework import status
from rest_framework.reverse import reverse

from picklists.enums import PickListStatus, PicklistType
from test_helpers.clients import DataTestClient


class PicklistItemUpdate(DataTestClient):
    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item(
            "Picklist item", self.team, PicklistType.ECJU, PickListStatus.ACTIVE
        )
        self.url = reverse(
            "picklist_items:picklist_item", kwargs={"pk": self.picklist_item.id}
        )

    def test_deactivate_a_picklist_item(self):
        data = {"status": PickListStatus.DEACTIVATED}

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data["picklist_item"]["status"],
            {"key": PickListStatus.DEACTIVATED, "value": "Deactivated"},
        )

    def test_reactivate_a_picklist_item(self):
        self.picklist_item.status = PickListStatus.DEACTIVATED
        self.picklist_item.save()

        data = {"status": PickListStatus.ACTIVE}

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data["picklist_item"]["status"],
            {"key": PickListStatus.ACTIVE, "value": "Active"},
        )
