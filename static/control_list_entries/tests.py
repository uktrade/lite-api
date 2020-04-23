from django.urls import reverse
from rest_framework import status

from static.control_list_entries.models import ControlListEntry
from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class CLCListTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("static:control_list_entries:control_list_entries")

    def _validate_returned_clc(self, item, full_detail: bool):
        self.assertIsNotNone(item.get("rating"))
        self.assertIsNotNone(item.get("text"))
        if full_detail:
            self.assertIsNotNone(item.get("id"))
            self.assertIsNotNone(item.get("is_decontrolled"))
            children = item.get("children")
            if children:
                for child in children:
                    self._validate_returned_clc(child, full_detail=full_detail)

    def test_get_clc_list(self):
        response = self.client.get(self.url)
        response_data = response.json()["control_list_entries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response_data:
            self._validate_returned_clc(item, full_detail=True)

    def test_get_flattened_clc_list(self):
        response = self.client.get(self.url + "?flatten=True")
        response_data = response.json()["control_list_entries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response_data:
            self._validate_returned_clc(item, full_detail=False)


class CLCTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.parent_rating = ControlListEntry.objects.create(rating="Xyz123", text="Parent rating", parent=None, is_decontrolled=False)
        self.child_rating = ControlListEntry.objects.create(rating="Xyz123b", text="Child 1", parent=self.parent_rating, is_decontrolled=False)
        self.url = "static:control_list_entries:control_list_entry"

    def test_get_clc_with_parent(self):
        url = reverse(self.url, kwargs={"rating": self.child_rating.rating},)
        response = self.client.get(url)
        response_data = response.json()["control_list_entry"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.child_rating.id))
        self.assertEqual(response_data["rating"], self.child_rating.rating)
        self.assertEqual(response_data["text"], self.child_rating.text)
        self.assertEqual(response_data["is_decontrolled"], self.child_rating.is_decontrolled)
        self.assertEqual(response_data["parent"]["id"], str(self.parent_rating.id))
        self.assertEqual(response_data["parent"]["rating"], self.parent_rating.rating)
        self.assertEqual(response_data["parent"]["text"], self.parent_rating.text)
        self.assertEqual(response_data["parent"]["is_decontrolled"], self.parent_rating.is_decontrolled)

    def test_get_clc_with_children(self):
        child_2 = ControlListEntry.objects.create(rating="ML1d1", text="Child 2-1", parent=self.parent_rating, is_decontrolled=False)

        url = reverse(self.url, kwargs={"rating": self.parent_rating.rating},)
        response = self.client.get(url)
        response_data = response.json()["control_list_entry"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.parent_rating.id))
        self.assertEqual(response_data["rating"], self.parent_rating.rating)
        self.assertEqual(response_data["text"], self.parent_rating.text)
        self.assertEqual(response_data["is_decontrolled"], self.parent_rating.is_decontrolled)
        self.assertEqual(len(response_data["children"]), 2)
        for child in [self.child_rating, child_2]:
            self.assertTrue(str(child.id) in [item["id"] for item in response_data["children"]])
            self.assertTrue(child.rating in [item["rating"] for item in response_data["children"]])
            self.assertTrue(child.text in [item["text"] for item in response_data["children"]])
            self.assertTrue(child.is_decontrolled in [item["is_decontrolled"] for item in response_data["children"]])


class ControlListEntriesResponseTests(EndPointTests):
    url = "/static/control-list-entries/"

    def test_control_list_entries(self):
        self.call_endpoint(self.get_exporter(), self.url)

    def test_control_list_entries_flattened(self):
        self.call_endpoint(self.get_exporter(), self.url + "?flatten=True")
