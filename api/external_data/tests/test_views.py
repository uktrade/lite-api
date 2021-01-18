import os

from test_helpers.clients import DataTestClient

from django.core.management import call_command
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from api.external_data import models


class DenialViewSetTests(DataTestClient):
    def test_create_success(self):
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.Denial.objects.count(), 3)
        self.assertEqual(
            list(models.Denial.objects.values("reference", "name", "address", "data")),
            [
                {
                    "address": "123 fake street",
                    "data": {"field_one": "value_one", "field_two": "value_two", "field_n": "value_n"},
                    "name": "Jim Example",
                    "reference": "FOO123",
                },
                {
                    "address": "123 fake street",
                    "data": {"field_one": "value_one", "field_two": "value_two", "field_n": "value_n"},
                    "name": "Jak Example",
                    "reference": "BAR123",
                },
                {
                    "address": "123 fake street",
                    "data": {"field_one": "value_one", "field_two": "value_two", "field_n": "value_n"},
                    "name": "Bob Example",
                    "reference": "BAZ123",
                },
            ],
        )

    def test_create_validation_error(self):
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_invalid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "errors": {
                    "csv_file": [
                        "[Row 2] reference: This field may not be null.",
                        "[Row 3] reference: This field may not be null.",
                        "[Row 4] reference: This field may not be null.",
                    ]
                }
            },
        )

    def test_create_validation_error_diplicate(self):
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()

        response_one = self.client.post(url, {"csv_file": content}, **self.gov_headers)
        self.assertEqual(response_one.status_code, 201)

        response_two = self.client.post(url, {"csv_file": content}, **self.gov_headers)
        self.assertEqual(response_two.status_code, 400)
        self.assertEqual(
            response_two.json(),
            {
                "errors": {
                    "csv_file": [
                        "[Row 2] reference: denial with this reference already exists.",
                        "[Row 3] reference: denial with this reference already exists.",
                        "[Row 4] reference: denial with this reference already exists.",
                    ]
                }
            },
        )


class DenialSearchView(DataTestClient):
    @override_settings(ELASTICSEARCH_DENIALS_INDEX_ALIAS="denials-alias-test")
    def test_search(self):
        call_command("search_index", models=["external_data.denial"], action="rebuild", force=True)
        # given some denials exist
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.Denial.objects.count(), 3)

        # and one of them is revoked

        denial = models.Denial.objects.first()
        denial.is_revoked = True
        denial.save()

        # then only 2 denials will be returned when searching
        url = reverse("external_data:denial_search-list")

        response = self.client.get(url, {"search": "Example"}, **self.gov_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["hits"]["hits"]), 2)
