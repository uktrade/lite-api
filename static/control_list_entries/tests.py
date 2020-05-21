from django.urls import reverse
from rest_framework import status

from static.control_list_entries.factories import ControlListEntriesFactory
from static.control_list_entries.helpers import convert_control_list_entries_to_tree
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
            children = item.get("children")
            if children:
                for child in children:
                    self._validate_returned_clc(child, full_detail=full_detail)

    def test_get_clc_list(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["control_list_entries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response_data:
            self._validate_returned_clc(item, full_detail=True)

    def test_get_flattened_clc_list(self):
        response = self.client.get(self.url + "?flatten=True", **self.exporter_headers)
        response_data = response.json()["control_list_entries"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response_data:
            self._validate_returned_clc(item, full_detail=False)


class CLCTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.parent_rating = ControlListEntry.objects.create(rating="Xyz123", text="Parent rating", parent=None,)
        self.child_rating = ControlListEntry.objects.create(
            rating="Xyz123b", text="Child 1", parent=self.parent_rating,
        )
        self.url = "static:control_list_entries:control_list_entry"

    def _validate_clc(self, response_data, object):
        self.assertEqual(response_data["id"], str(object.id))
        self.assertEqual(response_data["rating"], object.rating)
        self.assertEqual(response_data["text"], object.text)

    def test_get_clc_with_parent(self):
        url = reverse(self.url, kwargs={"rating": self.child_rating.rating},)
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["control_list_entry"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._validate_clc(response_data, self.child_rating)
        self._validate_clc(response_data["parent"], self.parent_rating)

    def test_get_clc_with_children(self):
        child_2 = ControlListEntry.objects.create(rating="ML1d1", text="Child 2-1", parent=self.parent_rating)

        url = reverse(self.url, kwargs={"rating": self.parent_rating.rating},)
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["control_list_entry"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._validate_clc(response_data, self.parent_rating)
        self.assertEqual(len(response_data["children"]), 2)
        for child in [self.child_rating, child_2]:
            self.assertTrue(str(child.id) in [item["id"] for item in response_data["children"]])
            self.assertTrue(child.rating in [item["rating"] for item in response_data["children"]])
            self.assertTrue(child.text in [item["text"] for item in response_data["children"]])


class ControlListEntryHelpersTest(DataTestClient):
    def convert_control_list_entry_to_expected_format(self, control_list, children=None):
        json = {
            "id": control_list.id,
            "rating": control_list.rating,
            "text": control_list.text,
            "parent_id": control_list.parent_id,
            "category": control_list.category,
        }
        if children:
            json["children"] = children

        return json

    def setUp(self):
        super().setUp()
        # create 5 control lists in the form of a tree, and determine they come back in correct format from helper
        base = ControlListEntriesFactory(rating="abc1")
        base_child_1 = ControlListEntriesFactory(rating="abc1a", parent=base)
        base_child_2 = ControlListEntriesFactory(rating="abc1b", parent=base)
        child_1_child = self.convert_control_list_entry_to_expected_format(
            ControlListEntriesFactory(rating="abc1a1", parent=base_child_1)
        )
        child_2_child = self.convert_control_list_entry_to_expected_format(
            ControlListEntriesFactory(rating="abc1b1", parent=base_child_2)
        )

        base_child_1 = self.convert_control_list_entry_to_expected_format(base_child_1, [child_1_child])
        base_child_2 = self.convert_control_list_entry_to_expected_format(base_child_2, [child_2_child])

        self.expected_layout = [self.convert_control_list_entry_to_expected_format(base, [base_child_1, base_child_2])]

    def test_convert_control_list_entries_to_tree(self):
        qs = ControlListEntry.objects.filter(category="test-list")
        result = convert_control_list_entries_to_tree(qs)

        self.assertEqual(result, self.expected_layout)


class ControlListEntriesResponseTests(EndPointTests):
    url = "/static/control-list-entries/"

    def test_control_list_entries(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)

    def test_control_list_entries_flattened(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + "?flatten=True")
