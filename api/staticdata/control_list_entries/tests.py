from django.urls import reverse
from rest_framework import status

from api.static.control_list_entries.factories import ControlListEntriesFactory
from api.static.control_list_entries.helpers import convert_control_list_entries_to_tree
from api.static.control_list_entries.models import ControlListEntry
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
        self.parent_rating = ControlListEntriesFactory(rating="Xyz123", text="Parent rating")
        self.child_rating = ControlListEntriesFactory(rating="Xyz123b", text="Child 1", parent=self.parent_rating,)
        self.url = "static:control_list_entries:control_list_entry"

    def _validate_clc(self, response_data, object):
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
        child_2 = ControlListEntriesFactory(rating="ML1d1", text="Child 2-1", parent=self.parent_rating)

        url = reverse(self.url, kwargs={"rating": self.parent_rating.rating},)
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["control_list_entry"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._validate_clc(response_data, self.parent_rating)
        self.assertEqual(len(response_data["children"]), 2)
        for child in [self.child_rating, child_2]:
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

    def generate_group_of_ratings(self, rating_prefix, category="test-list"):
        # create 5 control lists in the form of a tree
        base = ControlListEntriesFactory(rating=f"{rating_prefix}1")
        base_child_1 = ControlListEntriesFactory(rating=f"{rating_prefix}1a", parent=base)
        base_child_2 = ControlListEntriesFactory(rating=f"{rating_prefix}1b", parent=base)
        child_1_child = self.convert_control_list_entry_to_expected_format(
            ControlListEntriesFactory(rating=f"{rating_prefix}1a1", parent=base_child_1)
        )
        child_2_child = self.convert_control_list_entry_to_expected_format(
            ControlListEntriesFactory(rating=f"{rating_prefix}1b1", parent=base_child_2)
        )

        base_child_1 = self.convert_control_list_entry_to_expected_format(base_child_1, [child_1_child])
        base_child_2 = self.convert_control_list_entry_to_expected_format(base_child_2, [child_2_child])

        return self.convert_control_list_entry_to_expected_format(base, [base_child_1, base_child_2])

    def test_convert_control_list_entries_to_tree(self):
        expected_result = [self.generate_group_of_ratings(rating_prefix="abc", category="test-list")]
        qs = ControlListEntry.objects.filter(category="test-list")
        result = convert_control_list_entries_to_tree(qs.values())

        self.assertEqual(result, expected_result)

    def test_multiple_groups(self):
        expected_result = [
            self.generate_group_of_ratings(rating_prefix="abc", category="test-list"),
            self.generate_group_of_ratings(rating_prefix="xyz", category="another-list"),
        ]

        qs = ControlListEntry.objects.filter(category__in=["test-list", "another-list"])
        result = convert_control_list_entries_to_tree(qs.values())

        self.assertEqual(result, expected_result)


class ControlListEntriesResponseTests(EndPointTests):
    url = "/static/control-list-entries/"

    def test_control_list_entries(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)

    def test_control_list_entries_flattened(self):
        self.call_endpoint(self.get_exporter_headers(), self.url + "?flatten=True")
