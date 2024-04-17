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
                    "reference": "DN2000/0000",
                    "regime_reg_ref": "AB-CD-EF-000",
                    "name": "Organisation Name",
                    "address": "1000 Street Name, City Name",
                    "notifying_government": "Country Name",
                    "country": "Country Name",
                    "item_list_codes": "0A00100",
                    "item_description": "Medium Size Widget",
                    "consignee_name": "Example Name",
                    "end_use": "Used in industry",
                    "reason_for_refusal": "Risk of outcome",
                    "spire_entity_id": 123,
                    "data": {},
                },
                {
                    "reference": "DN2000/0010",
                    "regime_reg_ref": "AB-CD-EF-300",
                    "name": "Organisation Name 3",
                    "address": "2001 Street Name, City Name 3",
                    "notifying_government": "Country Name 3",
                    "country": "Country Name 3",
                    "item_list_codes": "0A00201",
                    "item_description": "Unspecified Size Widget",
                    "consignee_name": "Example Name 3",
                    "end_use": "Used in other industry",
                    "reason_for_refusal": "Risk of outcome 3",
                    "spire_entity_id": 125,
                    "data": {},
                },
                {
                    "reference": "DN2010/0001",
                    "regime_reg_ref": "AB-XY-EF-900",
                    "name": "The Widget Company",
                    "address": "2 Example Road, Example City",
                    "notifying_government": "Example Country",
                    "country": "Country Name X",
                    "item_list_codes": "catch all",
                    "item_description": "Extra Large Size Widget",
                    "consignee_name": "Example Name 4",
                    "end_use": "Used in unknown industry",
                    "reason_for_refusal": "Risk of outcome 4",
                    "spire_entity_id": 126,
                    "data": {},
                },
                {
                    "reference": "DN3000/0000",
                    "regime_reg_ref": "AB-CD-EF-100",
                    "name": "Organisation Name XYZ",
                    "address": "2000 Street Name, City Name 2",
                    "notifying_government": "Country Name 2",
                    "country": "Country Name 2",
                    "item_list_codes": "0A00200",
                    "item_description": "Large Size Widget",
                    "consignee_name": "Example Name 2",
                    "end_use": "Used in other industry",
                    "reason_for_refusal": "Risk of outcome 2",
                    "spire_entity_id": 124,
                    "data": {},
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

    def test_create_error_missing_required_headers(self):
        url = reverse("external_data:denial-list")
        # missing the 'reference' header
        content = """
        regime_reg_ref,name,address,notifying_government,country,item_list_codes,item_description,consignee_name,end_use,reason_for_refusal,spire_entity_id
        AB-CD-EF-000,Organisation Name,"1000 Street Name, City Name",Country Name,Country Name,0A00100,Medium Size Widget,Example Name,Used in industry,Risk of outcome,123
        """
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"errors": {"csv_file": ["Missing required headers in CSV file"]}})

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
            ({"search": "address:Street Name"}, 3),
            ({"search": "address:Example"}, 1),
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
