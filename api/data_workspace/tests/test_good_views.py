from django.test import override_settings
from api.goods.models import GoodControlListEntry
from api.staticdata.control_list_entries.models import ControlListEntry
from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class DataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.good = DataTestClient.create_good(description="Test good", organisation=self.organisation)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=False)
    def test_goods(self):
        url = reverse("data_workspace:dw-goods-list")
        expected_fields = (
            "id",
            "name",
            "description",
            "part_number",
            "control_list_entries",
            "comment",
            "is_good_controlled",
            "report_summary",
            "flags",
            "documents",
            "is_pv_graded",
            "grading_comment",
            "pv_grading_details",
            "status",
            "item_category",
            "is_military_use",
            "is_component",
            "uses_information_security",
            "modified_military_use_details",
            "component_details",
            "information_security_details",
            "is_document_available",
            "is_document_sensitive",
            "no_document_comments",
            "software_or_technology_details",
            "firearm_details",
            "is_precedent",
            "precedents",
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=False)
    def test_good_control_list_entry(self):
        clc_entry = ControlListEntry.objects.first()
        GoodControlListEntry.objects.create(good=self.good, controllistentry=clc_entry)
        url = reverse("data_workspace:dw-good-control-list-entries-list")
        expected_fields = ("id", "good", "controllistentry")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)
