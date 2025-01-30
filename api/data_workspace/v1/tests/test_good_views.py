from django.test import override_settings
from api.goods.models import GoodControlListEntry
from api.goods.tests.factories import GoodFactory
from api.staticdata.control_list_entries.models import ControlListEntry
from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class DataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.good = GoodFactory(name="Test good", organisation=self.organisation)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=False)
    def test_goods(self):
        url = reverse("data_workspace:v1:dw-goods-list")
        expected_fields = set(
            [
                "id",
                "name",
                "description",
                "part_number",
                "control_list_entries",
                "is_good_controlled",
                "status",
                "item_category",
                "is_pv_graded",
                "report_summary",
            ]
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(set(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(set(options.keys()), expected_fields)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=False)
    def test_good_control_list_entry(self):
        clc_entry = ControlListEntry.objects.first()
        GoodControlListEntry.objects.create(good=self.good, controllistentry=clc_entry)
        url = reverse("data_workspace:v1:dw-good-control-list-entries-list")
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
