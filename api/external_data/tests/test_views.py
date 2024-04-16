import os

from elasticsearch_dsl import Index
from parameterized import parameterized
import pytest

from django.core.management import call_command
from django.conf import settings
from django.urls import reverse

from api.external_data import documents, models, serializers
from test_helpers.clients import DataTestClient


class DenialViewSetTests(DataTestClient):
    def test_create_success(self):
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.DenialEntity.objects.count(), 4)
        self.assertEqual(
            list(models.DenialEntity.objects.values(*serializers.DenialFromCSVFileSerializer.required_headers, "data")),
            [
                {
                    "address": "123 fake street",
                    "consignee_name": "Fred Food",
                    "data": {"end_user_flag": "true", "consignee_flag": "true", "other_role": "false"},
                    "country": "Germany",
                    "item_description": "Foo",
                    "item_list_codes": "ABC123",
                    "name": "Jim Example",
                    "notifying_government": "France",
                    "end_use": "used in car",
                    "reference": "FOO123",
                },
                {
                    "address": "123 fake street",
                    "consignee_name": "Fred Food",
                    "data": {"end_user_flag": "false", "consignee_flag": "true", "other_role": "false"},
                    "country": "Germany",
                    "item_description": "Foo",
                    "item_list_codes": "ABC123",
                    "name": "Jak Example",
                    "notifying_government": "France",
                    "end_use": "used in car",
                    "reference": "BAR123",
                },
                {
                    "address": "123 fake street",
                    "consignee_name": "Fred Food",
                    "data": {"end_user_flag": "false", "consignee_flag": "false", "other_role": "true"},
                    "country": "Germany",
                    "item_description": "Foo",
                    "item_list_codes": "ABC123",
                    "name": "Bob Example",
                    "notifying_government": "France",
                    "end_use": "used in car",
                    "reference": "BAG124",
                },
                {
                    "address": "Bob Avenue",
                    "consignee_name": "Fred Food",
                    "data": {"end_user_flag": "false", "consignee_flag": "false", "other_role": "true"},
                    "country": "Germany",
                    "item_description": "Foo",
                    "item_list_codes": "ABC123",
                    "name": "James Jones",
                    "notifying_government": "France",
                    "end_use": "used in car",
                    "reference": "BAT123",
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

    @pytest.mark.skip(
        reason="Unique constraint on reference is removed temporarily, enable this test once we reinstate that constraint"
    )
    def test_create_validation_error_duplicate(self):
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


class DenialSearchViewTests(DataTestClient):
    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({},),
            ({"page": 1},),
        ]
    )
    def test_populate_denial_entity_objects(self, page_query):
        call_command("search_index", models=["external_data.denialentity"], action="rebuild", force=True)
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.DenialEntity.objects.count(), 4)

        # Set one of them as revoked
        denial_entity = models.DenialEntity.objects.get(name="Organisation Name")
        denial_entity.is_revoked = True
        denial_entity.save()

        # Then only 2 denial entity objects will be returned when searching
        url = reverse("external_data:denial_search-list")

        response = self.client.get(url, {**page_query, "search": "name:Organisation Name XYZ"}, **self.gov_headers)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        expected_result = {
            "address": "2000 Street Name, City Name 2",
            "country": "Country Name 2",
            "item_description": "Large Size Widget",
            "item_list_codes": "0A00200",
            "name": "Organisation Name XYZ",
            "notifying_government": "Country Name 2",
            "end_use": "Used in other industry",
            "reference": "DN3000/0000",
        }

        for key, value in expected_result.items():
            self.assertEqual(response_json["results"][0][key], value)
        self.assertEqual(len(response_json["results"]), 2)
        self.assertEqual(response_json["total_pages"], 1)
        assert "entity_type" in response_json["results"][0]

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "name:Organisation Name"}, 3),
            ({"search": "name:The Widget Company"}, 1),
            ({"search": "name:XYZ"}, 1),
        ]
    )
    def test_denial_entity_search(self, query, quantity):
        call_command("search_index", models=["external_data.denialentity"], action="rebuild", force=True)
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(response.status_code, 201)

        url = reverse("external_data:denial_search-list")

        response = self.client.get(url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(len(response_json["results"]), quantity)

    @pytest.mark.elasticsearch
    def test_search(self):
        Index("sanctions-alias-test").create(ignore=[400])

        url = reverse("external_data:sanction-search")

        response = self.client.get(f"{url}?name=foo", **self.gov_headers)

        self.assertEqual(response.status_code, 200)
