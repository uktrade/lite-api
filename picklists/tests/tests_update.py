from rest_framework import status
from rest_framework.reverse import reverse

from audit_trail.payload import AuditType
from picklists.enums import PickListStatus, PicklistType
from test_helpers.clients import DataTestClient


class PicklistItemUpdate(DataTestClient):
    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item(
            "Picklist item", self.team, PicklistType.ECJU, PickListStatus.ACTIVE
        )
        self.url = reverse("picklist_items:picklist_item", kwargs={"pk": self.picklist_item.id})

    def test_deactivate_a_picklist_item(self):
        data = {"status": PickListStatus.DEACTIVATED}

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()
        picklist = self.client.get(self.url, **self.gov_headers).json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data["picklist_item"]["status"], {"key": PickListStatus.DEACTIVATED, "value": "Deactivated"},
        )
        self.assertEqual(picklist["picklist_item"]["activity"][0]["text"], f"{AuditType.DEACTIVATE_PICKLIST.value}.")

    def test_reactivate_a_picklist_item(self):
        self.picklist_item.status = PickListStatus.DEACTIVATED
        self.picklist_item.save()

        data = {"status": PickListStatus.ACTIVE}

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()
        picklist = self.client.get(self.url, **self.gov_headers).json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data["picklist_item"]["status"], {"key": PickListStatus.ACTIVE, "value": "Active"},
        )
        self.assertEqual(picklist["picklist_item"]["activity"][0]["text"], f"{AuditType.REACTIVATE_PICKLIST.value}.")

    def test_edit_a_picklist_item_name(self):
        old_name = self.picklist_item.name
        new_name = "New name"
        data = {"name": new_name}

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()
        picklist = self.client.get(self.url, **self.gov_headers).json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data["picklist_item"]["name"], new_name,
        )

        self.assertEqual(
            picklist["picklist_item"]["activity"][0]["text"],
            f"{AuditType.UPDATED_PICKLIST_NAME.value.format(old_name=old_name, new_name=new_name)}.",
        )

    def test_edit_a_picklist_item_text(self):
        old_text = self.picklist_item.text
        new_text = "New text"
        data = {"text": new_text}

        response = self.client.put(self.url, data, **self.gov_headers)
        response_data = response.json()
        picklist = self.client.get(self.url, **self.gov_headers).json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data["picklist_item"]["text"], new_text,
        )

        self.assertEqual(
            picklist["picklist_item"]["activity"][0]["text"],
            f"{AuditType.UPDATED_PICKLIST_TEXT.value.format(old_text=old_text, new_text=new_text)}.",
        )
