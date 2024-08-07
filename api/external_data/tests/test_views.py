import os

from elasticsearch_dsl import Index
from parameterized import parameterized
import pytest
from rest_framework import status

from django.core.management import call_command
from django.conf import settings
from django.urls import reverse

from api.external_data import models, serializers
from test_helpers.clients import DataTestClient

denial_data_fields = [
    "reference",
    "regime_reg_ref",
    "notifying_government",
    "denial_cle",
    "item_description",
    "end_use",
    "reason_for_refusal",
]


class DenialViewSetTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            self.CSV_DENIAL_COUNT = len(f.readlines()) - 1

    def test_create_success(self):
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.DenialEntity.objects.count(), self.CSV_DENIAL_COUNT)
        self.assertEqual(models.Denial.objects.count(), self.CSV_DENIAL_COUNT)
        self.assertEqual(
            list(
                models.DenialEntity.objects.values(
                    *serializers.DenialFromCSVFileSerializer.required_headers_denial_entity
                )
            ),
            [
                {
                    "name": "Organisation Name",
                    "address": "1000 Street Name, City Name",
                    "country": "Country Name",
                    "entity_type": "end_user",
                },
                {
                    "name": "Organisation Name 3",
                    "address": "2001 Street Name, City Name 3",
                    "country": "Country Name 3",
                    "entity_type": "consignee",
                },
                {
                    "name": "The Widget Company",
                    "address": "2 Example Road, Example City",
                    "country": "Country Name X",
                    "entity_type": "end_user",
                },
                {
                    "name": "Organisation Name XYZ",
                    "address": "2000 Street Name, City Name 2",
                    "country": "Country Name 2",
                    "entity_type": "third_party",
                },
                {
                    "name": "UK Issued",
                    "address": "2000 main road, some place",
                    "country": "Country Name 3",
                    "entity_type": "third_party",
                },
                {
                    "name": "Forward slash",
                    "address": "30/1 ltd",
                    "country": "Country Name 4",
                    "entity_type": "third_party",
                },
                {
                    "name": "c/o ltd",
                    "address": "forward slash",
                    "country": "Country Name 6",
                    "entity_type": "third_party",
                },
            ],
        )
        self.assertEqual(
            list(models.Denial.objects.values(*serializers.DenialFromCSVFileSerializer.required_headers_denial)),
            [
                {
                    "reference": "DN2000/0000",
                    "regime_reg_ref": "AB-CD-EF-000",
                    "notifying_government": "Country Name",
                    "denial_cle": "0A00100",
                    "item_description": "Medium Size Widget",
                    "end_use": "Used in industry",
                    "reason_for_refusal": "Risk of outcome",
                },
                {
                    "reference": "DN2000/0010",
                    "regime_reg_ref": "AB-CD-EF-300",
                    "notifying_government": "Country Name 3",
                    "denial_cle": "0A00201",
                    "item_description": "Unspecified Size Widget",
                    "end_use": "Used in other industry",
                    "reason_for_refusal": "Risk of outcome 3",
                },
                {
                    "reference": "",
                    "regime_reg_ref": "AB-XY-EF-900",
                    "notifying_government": "Example Country",
                    "denial_cle": "catch all",
                    "item_description": "Extra Large Size Widget",
                    "end_use": "Used in unknown industry",
                    "reason_for_refusal": "Risk of outcome 4",
                },
                {
                    "reference": "DN3000/0000",
                    "regime_reg_ref": "AB-CD-EF-100",
                    "notifying_government": "Country Name 2",
                    "denial_cle": "0A00200",
                    "item_description": "Large Size Widget",
                    "end_use": "Used in other industry",
                    "reason_for_refusal": "Risk of outcome 2",
                },
                {
                    "reference": "DN4000/0000",
                    "regime_reg_ref": "AB-CD-EF-200",
                    "notifying_government": "United Kingdom",
                    "denial_cle": "0A00300",
                    "item_description": "Large Size Widget",
                    "end_use": "Used in other industry",
                    "reason_for_refusal": "Risk of outcome 2",
                },
                {
                    "reference": "DN4102/0001",
                    "regime_reg_ref": "AB-CD-EF-400",
                    "notifying_government": "Country Name 4",
                    "denial_cle": "0A00504",
                    "item_description": "Large Size Widget",
                    "end_use": "Used in other industry",
                    "reason_for_refusal": "Risk of outcome 2",
                },
                {
                    "reference": "DN4103/0001",
                    "regime_reg_ref": "AB-CD-EF-500",
                    "notifying_government": "Country Name 5",
                    "denial_cle": "0A0050",
                    "item_description": "Large Size Widget",
                    "end_use": "Used in other industry",
                    "reason_for_refusal": "Risk of outcome 2",
                },
            ],
        )

    def test_create_error_missing_required_headers(self):
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_invalid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"errors": {"csv_file": ["Missing required headers in CSV file"]}})

    def test_create_and_set_entity_type(self):
        url = reverse("external_data:denial-list")
        content = """
        reference,regime_reg_ref,name,address,notifying_government,country,denial_cle,item_description,end_use,reason_for_refusal,entity_type
        DN2000/0000,AB-CD-EF-000,Organisation Name,"1000 Street Name, City Name",Country Name,Country Name,0A00100,Medium Size Widget,Used in industry,Risk of outcome,end_user
        DN2000/0010,AB-CD-EF-300,Organisation Name 3,"2001 Street Name, City Name 3",Country Name 3,Country Name 3,0A00201,Unspecified Size Widget,Used in other industry,Risk of outcome 3,consignee
        DN2010/0001,AB-XY-EF-900,The Widget Company,"2 Example Road, Example City",Example Country,Country Name X,"catch all",Extra Large Size Widget,Used in unknown industry,Risk of outcome 4,third_party
        DN3000/0000,AB-CD-EF-100,Organisation Name XYZ,"2000 Street Name, City Name 2",Country Name 2,Country Name 2,0A00200,Large Size Widget,Used in other industry,Risk of outcome 2,end_user
        """
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.DenialEntity.objects.count(), 4)
        self.assertEqual(
            list(
                models.DenialEntity.objects.values(
                    *serializers.DenialFromCSVFileSerializer.required_headers_denial_entity
                )
            ),
            [
                {
                    "name": "Organisation Name",
                    "address": "1000 Street Name, City Name",
                    "country": "Country Name",
                    "entity_type": "end_user",
                },
                {
                    "name": "Organisation Name 3",
                    "address": "2001 Street Name, City Name 3",
                    "country": "Country Name 3",
                    "entity_type": "consignee",
                },
                {
                    "name": "The Widget Company",
                    "address": "2 Example Road, Example City",
                    "country": "Country Name X",
                    "entity_type": "third_party",
                },
                {
                    "name": "Organisation Name XYZ",
                    "address": "2000 Street Name, City Name 2",
                    "country": "Country Name 2",
                    "entity_type": "end_user",
                },
            ],
        )

    def test_update_success(self):
        url = reverse("external_data:denial-list")
        content = """
        reference,regime_reg_ref,name,address,notifying_government,country,denial_cle,item_description,end_use,reason_for_refusal,entity_type
        DN2000/0000,AB-CD-EF-000,Organisation Name,"1000 Street Name, City Name",Country Name,Country Name,0A00100,Medium Size Widget,Used in industry,Risk of outcome,end_user
        """

        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.Denial.objects.count(), 1)
        self.assertEqual(models.DenialEntity.objects.count(), 1)

        self.assertEqual(
            list(models.Denial.objects.values(*denial_data_fields)),
            [
                {
                    "reference": "DN2000/0000",
                    "regime_reg_ref": "AB-CD-EF-000",
                    "notifying_government": "Country Name",
                    "denial_cle": "0A00100",
                    "item_description": "Medium Size Widget",
                    "end_use": "Used in industry",
                    "reason_for_refusal": "Risk of outcome",
                },
            ],
        )
        self.assertEqual(
            list(
                models.DenialEntity.objects.values(
                    *serializers.DenialFromCSVFileSerializer.required_headers_denial_entity
                )
            ),
            [
                {
                    "name": "Organisation Name",
                    "address": "1000 Street Name, City Name",
                    "country": "Country Name",
                    "entity_type": "end_user",
                },
            ],
        )
        updated_content = """
        reference,regime_reg_ref,name,address,notifying_government,country,denial_cle,item_description,end_use,reason_for_refusal,entity_type
        DN2000/0000,AB-CD-EF-000,Organisation Name,"1000 Street Name, City Name",Country Name 2,Country Name 2,0A00200,Medium Size Widget 2, Used in industry 2,Risk of outcome 2,end_user
        """
        response = self.client.post(url, {"csv_file": updated_content}, **self.gov_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.Denial.objects.count(), 1)
        self.assertEqual(models.DenialEntity.objects.count(), 1)
        self.assertEqual(
            list(models.Denial.objects.values(*denial_data_fields)),
            [
                {
                    "reference": "DN2000/0000",
                    "regime_reg_ref": "AB-CD-EF-000",
                    "notifying_government": "Country Name 2",
                    "denial_cle": "0A00200",
                    "item_description": "Medium Size Widget 2",
                    "end_use": "Used in industry 2",
                    "reason_for_refusal": "Risk of outcome 2",
                }
            ],
        )
        self.assertEqual(
            list(
                models.DenialEntity.objects.values(
                    *serializers.DenialFromCSVFileSerializer.required_headers_denial_entity
                )
            ),
            [
                {
                    "name": "Organisation Name",
                    "address": "1000 Street Name, City Name",
                    "country": "Country Name 2",
                    "entity_type": "end_user",
                }
            ],
        )

    def test_create_error_serializer_errors(self):
        url = reverse("external_data:denial-list")
        content = """reference,regime_reg_ref,name,address,notifying_government,country,denial_cle,item_description,end_use,reason_for_refusal,entity_type
        DN2000/0000,,Organisation Name,"1000 Street Name, City Name",Country Name,Country Name,0A00100,Medium Size Widget,Used in industry,Risk of outcome,end_user
        """
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"errors": {"csv_file": ["[Row 1] regime_reg_ref: This field may not be blank."]}}
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

    def test_create_sanitise_csv(self):
        url = reverse("external_data:denial-list")
        content = """
        reference,regime_reg_ref,name,address,notifying_government,country,denial_cle,item_description,end_use,reason_for_refusal,entity_type
        DN2000/0000,AB-CD-EF-000,Organisation Name,"<script>bad xss script</script>",Country Name,Country Name,0A00100,Medium Size Widget,Used in industry,Risk of outcome,end_user
        """
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(
            list(models.DenialEntity.objects.values("address")),
            [{"address": "&lt;script&gt;bad xss script&lt;/script&gt;"}],
        )

        self.assertEqual(response.status_code, 201)


class DenialSearchViewTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            self.CSV_DENIAL_COUNT = len(f.readlines()) - 1

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
        self.assertEqual(models.DenialEntity.objects.count(), self.CSV_DENIAL_COUNT)

        # Set one of them as revoked
        denial_entity = models.DenialEntity.objects.get(name="Organisation Name")
        denial_entity.denial.is_revoked = True
        denial_entity.denial.save()
        # This needs to be fixed we need to rebuild index if child value is updated.
        # Then only 2 denial entity objects will be returned when searching
        url = reverse("external_data:denial_search-list")

        response = self.client.get(url, {**page_query, "search": "name:(Organisation Name XYZ)"}, **self.gov_headers)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        expected_result = {
            "address": "2000 Street Name, City Name 2",
            "country": "Country Name 2",
            "item_description": "Large Size Widget",
            "denial_cle": "0A00200",
            "name": "<mark>Organisation</mark> <mark>Name</mark> <mark>XYZ</mark>",
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
            ("name:Organisation Name XYZ", {"name": "<mark>Organisation</mark> <mark>Name</mark> <mark>XYZ</mark>"}),
            ("denial_cle:0A00200", {"denial_cle": "<mark>0A00200</mark>"}),
            ("address:2000", {"address": "<mark>2000</mark> Street Name, City Name 2"}),
        ]
    )
    def test_search_highlighting(self, search_query, expected_result):
        call_command("search_index", models=["external_data.denialentity"], action="rebuild", force=True)
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)
        self.assertEqual(response.status_code, 201)

        url = reverse("external_data:denial_search-list")

        response = self.client.get(url, {"search": search_query}, **self.gov_headers)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        key, value = list(expected_result.items())[0]

        self.assertEqual(response_json["results"][0][key], value)

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "name:(Organisation Name)"}, ["AB-CD-EF-000", "AB-CD-EF-300", "AB-CD-EF-100"]),
            ({"search": "name:(The Widget Company)"}, ["AB-XY-EF-900"]),
            ({"search": "name:(XYZ)"}, ["AB-CD-EF-100"]),
            ({"search": "address:(Street Name)"}, ["AB-CD-EF-000", "AB-CD-EF-300", "AB-CD-EF-100"]),
            ({"search": "address:(Example)"}, ["AB-XY-EF-900"]),
            ({"search": "name:(UK Issued)"}, []),
            ({"search": "denial_cle:(catch all)"}, ["AB-XY-EF-900"]),
            (
                {"search": "name:(Widget) OR address:(2001)"},
                [
                    "AB-XY-EF-900",
                    "AB-CD-EF-300",
                ],
            ),
            ({"search": "name:(Organisation) AND address:(2000)"}, ["AB-CD-EF-100"]),
            ({"search": "address:(30/1)"}, ["AB-CD-EF-400"]),
            ({"search": "name:(c/o)"}, ["AB-CD-EF-500"]),
        ]
    )
    def test_denial_entity_search(self, query, expected_items):
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
        regime_reg_ref_results = [r["regime_reg_ref"] for r in response_json["results"]]
        self.assertListEqual(regime_reg_ref_results, expected_items)

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "name:(Organisation Name)"}, True),
            ({"search": "name:(The Widget Company)"}, True),
            ({"search": "name:(dfgklmdsgm)"}, False),
            ({"search": "address:(Street Name)"}, True),
        ]
    )
    def test_denial_entity_search_scores(self, query, expected_items):
        call_command("search_index", models=["external_data.denialentity"], action="rebuild", force=True)
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()

        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)
        url = reverse("external_data:denial_search-list")

        response = self.client.get(url, query, **self.gov_headers)
        response_json = response.json()
        search_score_results = [r["search_score"] for r in response_json["results"]]

        self.assertEqual(expected_items, any(isinstance(item, float) for item in search_score_results))

    def test_denial_entity_search_invalid_query(self):
        call_command("search_index", models=["external_data.denialentity"], action="rebuild", force=True)
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
        response = self.client.post(url, {"csv_file": content}, **self.gov_headers)

        self.assertEqual(response.status_code, 201)

        url = reverse("external_data:denial_search-list")
        query = {"search": "ejfhke&**&*7&&^*(£)"}
        response = self.client.get(url, query, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = response.json()
        self.assertEqual(response["errors"]["search"], "Invalid search string")

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            (
                {"search": "address:(Street Name, Springfield)"},
                [
                    "1000 Street <mark>Name</mark>, City <mark>Name</mark>",
                    "2001 Street <mark>Name</mark>, City <mark>Name</mark> 3",
                    "2000 Street <mark>Name</mark>, City <mark>Name</mark> 2",
                ],
            ),
            (
                {"search": "address:(\Example\ Avenue, Townsville)"},
                ["2 <mark>Example</mark> Road, <mark>Example</mark> City"],
            ),
            ({"search": "address:(road,)"}, []),
        ]
    )
    def test_denial_search_with_chars(self, query, expected_items):
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
        search_results = [r["address"] for r in response_json["results"]]

        self.assertEqual(search_results, expected_items)

    @pytest.mark.elasticsearch
    def test_search(self):
        Index("sanctions-alias-test").create(ignore=[400])

        url = reverse("external_data:sanction-search")

        response = self.client.get(f"{url}?name=foo", **self.gov_headers)

        self.assertEqual(response.status_code, 200)
