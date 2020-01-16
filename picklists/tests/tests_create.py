from django.urls import reverse
from rest_framework import status

from audit_trail.payload import AuditType
from picklists.enums import PicklistType, PickListStatus
from test_helpers.clients import DataTestClient


class PicklistItemCreate(DataTestClient):
    def setUp(self):
        super().setUp()
        self.data = {
            "name": "picklist entry name",
            "text": "ats us nai",
            "type": PicklistType.ECJU,
            "team": str(self.team.id),
            "status": PickListStatus.ACTIVE,
        }
        self.url = reverse("picklist_items:picklist_items")

    def test_gov_user_can_add_item_to_picklist(self):
        response = self.client.post(self.url, self.data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["picklist_item"]["name"], self.data["name"])
        self.assertEqual(response_data["picklist_item"]["text"], self.data["text"])
        self.assertEqual(response_data["picklist_item"]["type"]["key"], self.data["type"])
        self.assertEqual(response_data["picklist_item"]["team"], self.data["team"])
        self.assertEqual(response_data["picklist_item"]["status"]["key"], self.data["status"])

    def test_add_item_to_picklist_audit(self):
        response = self.client.post(self.url, self.data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse("picklist_items:picklist_item", kwargs={"pk": response.json()["picklist_item"]["id"]})
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["picklist_item"]["activity"][0]["text"], f"{AuditType.CREATED_PICKLIST.value}.",
        )
