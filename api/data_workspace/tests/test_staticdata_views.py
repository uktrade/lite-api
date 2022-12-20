from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class DataWorkspaceTests(DataTestClient):
    def test_control_list_entries(self):
        url = reverse("data_workspace:dw-control-list-entries-list")
        expected_fields = ("id", "rating", "text", "category", "controlled", "parent")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_countries(self):
        url = reverse("data_workspace:dw-countries-list")
        expected_fields = ("id", "name", "type", "is_eu", "report_name")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_case_statuses(self):
        url = reverse("data_workspace:dw-case-statuses-list")
        expected_fields = ("id", "key", "value", "status", "priority")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_regimes(self):
        url = reverse("data_workspace:dw-regimes-list")
        expected_fields = ("id", "name")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_regime_subsections(self):
        url = reverse("data_workspace:dw-regime-subsections-list")
        expected_fields = ("id", "name", "regime")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_regime_entries(self):
        url = reverse("data_workspace:dw-regime-entries-list")
        expected_fields = ("id", "name", "shortened_name", "subsection")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["GET"]
        self.assertEqual(tuple(options.keys()), expected_fields)
