import uuid
from copy import deepcopy

from django.utils import timezone
from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from api.goods.enums import (
    GoodPvGraded,
    PvGrading,
    GoodStatus,
    ItemCategory,
    MilitaryUse,
    Component,
    FirearmGoodType,
)
from api.goods.models import Good
from lite_content.lite_api import strings
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from api.staticdata.control_list_entries.models import ControlListEntry
from test_helpers.clients import DataTestClient

URL = reverse("goods:goods")

REQUEST_DATA = {
    "name": f"Plastic bag {uuid.uuid4()}",
    "description": "Plastic bag",
    "is_good_controlled": False,
    "control_list_entries": [],
    "part_number": "1337",
    "validate_only": False,
    "is_pv_graded": GoodPvGraded.NO,
    "pv_grading_details": {
        "grading": None,
        "custom_grading": "Custom Grading",
        "prefix": "Prefix",
        "suffix": "Suffix",
        "issuing_authority": "Issuing Authority",
        "reference": "ref123",
        "date_of_issue": "2019-12-25",
    },
    "item_category": ItemCategory.GROUP1_DEVICE,
    "is_military_use": MilitaryUse.NO,
    "is_component_step": True,
    "is_component": Component.NO,
    "is_military_use_step": True,
    "is_information_security_step": True,
    "uses_information_security": True,
    "modified_military_use_details": "",
}


def _assert_response_data(self, response_data, request_data):
    self.assertEquals(response_data["description"], request_data["description"])
    self.assertEquals(response_data["part_number"], request_data["part_number"])
    self.assertEquals(response_data["status"]["key"], GoodStatus.DRAFT)
    self.assertEquals(response_data["item_category"]["key"], request_data["item_category"])
    self.assertEquals(response_data["is_military_use"]["key"], request_data["is_military_use"])

    if request_data["is_good_controlled"] == True:
        self.assertEquals(response_data["is_good_controlled"]["key"], "True")
        self.assertEquals(
            response_data["control_list_entries"], [{"rating": "ML1a", "text": get_control_list_entry("ML1a").text}]
        )

    if request_data["is_pv_graded"] == GoodPvGraded.YES:
        self.assertEquals(response_data["is_pv_graded"]["key"], GoodPvGraded.YES)

        response_data_pv_grading_details = response_data["pv_grading_details"]
        request_data_pv_grading_details = request_data["pv_grading_details"]

        if request_data_pv_grading_details["grading"]:
            grading_response = response_data_pv_grading_details.pop("grading")
            grading_request = request_data_pv_grading_details.pop("grading")
            self.assertEquals(grading_response["key"], grading_request)

        for key, value in request_data_pv_grading_details.items():
            self.assertEqual(response_data_pv_grading_details[key], value)


class CreateGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

        ControlListEntry.create("ML1b", "Info here", None)

    def test_when_creating_a_good_with_not_controlled_and_not_pv_graded_then_created_response_is_returned(self):
        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_pv_graded_and_controlled_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = True
        self.request_data["control_list_entries"] = ["ML1a"]
        self.request_data["is_pv_graded"] = GoodPvGraded.YES

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_pv_graded_set_to_null_then_bad_request_response_is_returned(self):
        self.request_data["is_pv_graded"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"is_pv_graded": ["This field may not be null."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_validate_only_then_ok_response_is_returned_and_good_is_not_created(self,):
        self.request_data["is_good_controlled"] = False
        self.request_data["is_pv_graded"] = GoodPvGraded.NO
        self.request_data["validate_only"] = True

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_that_is_not_controlled_success(self,):
        self.request_data["is_good_controlled"] = False

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_creating_a_good_that_is_not_controlled_multiple_clcs_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = False
        self.request_data["control_list_entries"] = ["ML1a", "ML1b"]

        response = self.client.post(URL, self.request_data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

        control_list_entries = response.json()["good"]["control_list_entries"]
        self.assertIn({"rating": "ML1a", "text": "Description"}, control_list_entries)
        self.assertIn({"rating": "ML1b", "text": "Info here"}, control_list_entries)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_add_good_no_item_category_selected_failure(self):
        data = {
            "name": f"Plastic bag {uuid.uuid4()}",
            "description": "good that doesn't belong to any category",
            "is_good_controlled": False,
            "validate_only": True,
            "is_pv_graded": GoodPvGraded.NO,
            "is_military_use": MilitaryUse.NO,
            "modified_military_use_details": "",
        }
        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["item_category"], [strings.Goods.FORM_NO_ITEM_CATEGORY_SELECTED])

    def test_add_good_no_description_provided_success(self):
        data = {
            "name": "Firearm",
            "is_good_controlled": False,
            "validate_only": True,
            "is_pv_graded": GoodPvGraded.NO,
            "is_military_use": MilitaryUse.NO,
            "item_category": ItemCategory.GROUP1_DEVICE,
            "uses_information_security": True,
            "modified_military_use_details": "",
        }
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_add_good_empty_name_provided_failure(self):
        data = {
            "name": "",
            "is_good_controlled": False,
            "validate_only": True,
            "is_pv_graded": GoodPvGraded.NO,
            "is_military_use": MilitaryUse.NO,
            "item_category": ItemCategory.GROUP1_DEVICE,
            "modified_military_use_details": "",
        }
        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["name"], ["Enter a product name"])

    def test_add_good_no_military_use_answer_selected_failure(self):
        data = {
            "name": "Firearm",
            "description": "Firearm product",
            "is_good_controlled": False,
            "validate_only": True,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP1_DEVICE,
            "is_military_use_step": True,
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["is_military_use"], [strings.Goods.FORM_NO_MILITARY_USE_SELECTED])

    def test_add_good_modified_military_use_answer_selected_no_details_provided_failure(self):
        """ Test failure when modified for military use is selected but no modification details are provided."""
        data = {
            "name": "Firearm",
            "description": "Firearm product",
            "is_good_controlled": False,
            "validate_only": True,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP1_DEVICE,
            "is_military_use": MilitaryUse.YES_MODIFIED,
            "is_military_use_step": True,
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["modified_military_use_details"], [strings.Goods.NO_MODIFICATIONS_DETAILS])

    def test_add_good_component_answer_not_selected_failure(self):
        data = {
            "name": "Firearm",
            "description": "Firearm product",
            "is_good_controlled": False,
            "validate_only": True,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP1_DEVICE,
            "is_military_use": MilitaryUse.NO,
            "is_military_use_step": True,
            "is_component_step": True,
            "modified_military_use_details": "",
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["is_component"], [strings.Goods.FORM_NO_COMPONENT_SELECTED])

    @parameterized.expand(
        [
            [Component.YES_DESIGNED, "designed_details", strings.Goods.NO_DESIGN_COMPONENT_DETAILS],
            [Component.YES_MODIFIED, "modified_details", strings.Goods.NO_MODIFIED_COMPONENT_DETAILS],
            [Component.YES_GENERAL_PURPOSE, "general_details", strings.Goods.NO_GENERAL_COMPONENT_DETAILS],
        ]
    )
    def test_add_good_component_not_details_provided_failure(self, component, details_field, details_error):
        """Test failure 'yes' component answer selected but no component details provided. """
        data = {
            "name": "Firearm",
            "description": "Firearm product",
            "is_good_controlled": False,
            "validate_only": True,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP1_DEVICE,
            "is_military_use": MilitaryUse.NO,
            "is_military_use_step": True,
            "is_component_step": True,
            "is_component": component,
            details_field: "",
            "modified_military_use_details": "",
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[details_field], [details_error])

    def test_add_good_information_security_not_selected_failure(self):
        data = {
            "name": "Firearm",
            "description": "Firearm product",
            "is_good_controlled": False,
            "validate_only": True,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP1_DEVICE,
            "is_military_use": MilitaryUse.NO,
            "is_military_use_step": True,
            "is_component_step": True,
            "is_component": Component.NO,
            "is_information_security_step": True,
            "modified_military_use_details": "",
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors["uses_information_security"], [strings.Goods.FORM_PRODUCT_DESIGNED_FOR_SECURITY_FEATURES]
        )

    def test_add_good_information_security_no_details_provided_success(self):
        data = {
            "name": "Firearm",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP1_DEVICE,
            "is_military_use": MilitaryUse.NO,
            "is_component_step": True,
            "is_component": Component.NO,
            "is_military_use_step": True,
            "is_information_security_step": True,
            "uses_information_security": True,
            "modified_military_use_details": "",
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(good["description"], data["description"])
        self.assertEquals(good["status"]["key"], GoodStatus.DRAFT)
        self.assertEquals(good["item_category"]["key"], data["item_category"])
        self.assertEquals(good["is_military_use"]["key"], data["is_military_use"])
        self.assertEqual(good["is_component"]["key"], data["is_component"])
        self.assertTrue(good["uses_information_security"])

    def test_add_good_information_security_details_provided_success(self):
        data = {
            "name": "Firearm",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP1_DEVICE,
            "is_military_use": MilitaryUse.NO,
            "is_military_use_step": True,
            "is_component_step": True,
            "is_component": Component.NO,
            "is_information_security_step": True,
            "uses_information_security": True,
            "information_security_details": "details about security",
            "modified_military_use_details": "",
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(good["description"], data["description"])
        self.assertEquals(good["status"]["key"], GoodStatus.DRAFT)
        self.assertEquals(good["item_category"]["key"], data["item_category"])
        self.assertEquals(good["is_military_use"]["key"], data["is_military_use"])
        self.assertEqual(good["is_component"]["key"], data["is_component"])
        self.assertTrue(good["uses_information_security"])
        self.assertEquals(good["information_security_details"], data["information_security_details"])

    @parameterized.expand(
        [[ItemCategory.GROUP3_SOFTWARE, "software details"], [ItemCategory.GROUP3_TECHNOLOGY, "technology details"]]
    )
    def test_add_category_three_good_success(self, category, details):
        data = {
            "name": "lite",
            "description": "Application software",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": category,
            "software_or_technology_details": details,
            "is_military_use": MilitaryUse.NO,
            "is_military_use_step": True,
            "modified_military_use_details": "",
            "is_software_or_technology_step": True,
            "is_information_security_step": True,
            "uses_information_security": True,
            "information_security_details": "details about security",
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(good["description"], data["description"])
        self.assertEquals(good["status"]["key"], GoodStatus.DRAFT)
        self.assertEquals(good["item_category"]["key"], data["item_category"])
        self.assertEquals(good["software_or_technology_details"], data["software_or_technology_details"])
        self.assertEquals(good["is_military_use"]["key"], data["is_military_use"])
        self.assertTrue(good["uses_information_security"])
        self.assertEquals(good["information_security_details"], data["information_security_details"])

    @parameterized.expand(
        [
            [ItemCategory.GROUP3_SOFTWARE, "", strings.Goods.FORM_NO_SOFTWARE_DETAILS],
            [ItemCategory.GROUP3_TECHNOLOGY, "", strings.Goods.FORM_NO_TECHNOLOGY_DETAILS],
        ]
    )
    def test_add_category_three_good_no_details_failure(self, category, details, error):
        data = {
            "name": "lite",
            "description": "Software application",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": category,
            "is_software_or_technology_step": True,
            "software_or_technology_details": details,
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["software_or_technology_details"], [error])

    def test_add_category_three_good_details_too_long_failure(self):
        data = {
            "name": "lite",
            "description": "Software application",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP3_TECHNOLOGY,
            "is_software_or_technology_step": True,
            "software_or_technology_details": "A" * 2001,
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors["software_or_technology_details"], ["Ensure this field has no more than 2000 characters."]
        )

    @parameterized.expand(
        [
            ["firearms", "Select yes if the product is a sporting shotgun"],
            ["ammunition", "Select yes if the product is sporting shotgun ammunition"],
            ["components_for_firearms", "Select yes if the product is a component of a sporting shotgun"],
            ["components_for_ammunition", "Select yes if the product is a component of sporting shotgun ammunition"],
            ["firearms_accessory", "Invalid firearm product type"],
            ["software_related_to_firearms", "Invalid firearm product type"],
            ["technology_related_to_firearms", "Invalid firearm product type"],
        ]
    )
    def test_add_firearms_type_sporting_shotgun_status_not_selected(self, firearm_type, error_msg):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {"type": firearm_type, "is_sporting_shotgun": None},
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["is_sporting_shotgun"], [error_msg])

    def test_add_category_two_good_no_type_selected_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {"type": None},
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["type"], [strings.Goods.FIREARM_GOOD_NO_TYPE])

    def test_add_firearms_type_replica_status_not_selected(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {"type": "firearms", "is_replica": None},
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["is_replica"][0], "Select yes if the product is a replica firearm")

    @parameterized.expand([["ammunition"], ["components_for_firearms"], ["components_for_ammunition"]])
    def test_add_firearms_replica_status_selected_for_invalid_types(self, firearm_type):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {"type": firearm_type, "is_replica": True},
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["is_replica"][0], "Invalid firearm product type")

    def test_add_firearms_replica_description_required(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {"type": "firearms", "is_replica": True, "replica_description": ""},
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["replica_description"], ["Enter description"])

    def test_add_category_two_good_no_year_of_manufacture_not_in_the_past_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": str(timezone.now().date().year + 1),
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["year_of_manufacture"], [strings.Goods.FIREARM_GOOD_YEAR_MUST_BE_IN_PAST])

    @parameterized.expand([[timezone.now().date().year], [timezone.now().date().year - 1]])
    def test_add_category_two_good_no_year_of_manufacture_in_the_past_success(self, year):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {"type": FirearmGoodType.AMMUNITION, "calibre": "0.5", "year_of_manufacture": str(year)},
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["firearm_details"]["year_of_manufacture"], year)

    def test_add_firearms_act_section_question_check_errors(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.FIREARMS,
                "calibre": "9mm",
                "year_of_manufacture": "2010",
                "is_covered_by_firearm_act_section_one_two_or_five": "",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "ABC123",
                "section_certificate_date_of_expiry": "2012-12-12",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(
            response["is_covered_by_firearm_act_section_one_two_or_five"][0],
            "Select yes if the product is covered by Section 1, Section 2 or Section 5 of the Firearms Act 1968",
        )

        data["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"] = "Yes"
        data["firearm_details"]["firearms_act_section"] = ""
        response = self.client.post(URL, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["firearms_act_section"][0], "Select which section the product is covered by")

    def test_add_firearms_certificate_missing_checks(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_missing": True,
                "section_certificate_missing_reason": "",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "2012-12-12",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(
            response["section_certificate_missing_reason"][0],
            "Enter a reason why you do not have a section 1 certificate",
        )

    def test_add_firearms_certificate_question_check_errors(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "2012-12-12",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["section_certificate_number"][0], "Enter the certificate number")

        data["firearm_details"]["section_certificate_number"] = "FR8C1604"
        data["firearm_details"]["section_certificate_date_of_expiry"] = None
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]

        self.assertEqual(
            response["section_certificate_date_of_expiry"][0],
            "Enter the certificate expiry date and include a day, month and year",
        )

    def test_add_firearms_certificate_missing_checks(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "1234",
                "section_certificate_missing": True,
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(
            response["section_certificate_missing_reason"][0],
            "Enter a reason why you do not have a section 1 certificate",
        )

        data["firearm_details"]["section_certificate_missing_reason"] = "Certificate not required"
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_add_category_two_good_no_section_certificate_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": None,
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            errors["is_covered_by_firearm_act_section_one_two_or_five"], [strings.Goods.FIREARM_GOOD_NO_SECTION]
        )

    def test_add_category_two_good_no_certificate_number_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": None,
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["section_certificate_number"], ["Enter the certificate number"])

    def test_add_category_two_good_no_certificate_expiry_date_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "ABC123",
                "section_certificate_date_of_expiry": None,
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            errors["section_certificate_date_of_expiry"],
            ["Enter the certificate expiry date and include a day, month and year"],
        )

    def test_add_category_two_good_certificate_number_in_past_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "ABC123",
                "section_certificate_date_of_expiry": "2012-12-12",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["section_certificate_date_of_expiry"], [strings.Goods.FIREARM_GOOD_INVALID_EXPIRY_DATE])

    def test_add_category_two_good_invalid_format_certificate_number_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "section_certificate_number": "ABC123",
                "section_certificate_date_of_expiry": "20-12-12",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            errors["section_certificate_date_of_expiry"], ["Enter the expiry date and include a day, month and year"],
        )

    def test_add_category_two_good_certificate_details_not_set_on_no_success(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "No",
                "section_certificate_number": "ABC123",
                "section_certificate_date_of_expiry": "2012-12-12",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(good["firearm_details"]["section_certificate_date_of_expiry"])
        self.assertIsNone(good["firearm_details"]["section_certificate_number"])
        self.assertEqual(good["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"], "No")

    def test_add_category_two_good_no_markings_answer_selected_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "No",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "",
                "has_identification_markings": "",
                "identification_markings_details": "",
                "no_identification_markings_details": "",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["has_identification_markings"], [strings.Goods.FIREARM_GOOD_NO_MARKINGS])

    def test_add_category_two_good_no_markings_selected_but_no_details_provided_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "No",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "",
                "has_identification_markings": "False",
                "identification_markings_details": "",
                "no_identification_markings_details": "",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            errors["no_identification_markings_details"], [strings.Goods.FIREARM_GOOD_NO_DETAILS_ON_NO_MARKINGS]
        )

    def test_add_category_two_good_yes_markings_selected_but_no_details_provided_failure(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "No",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "",
                "has_identification_markings": "True",
                "identification_markings_details": "",
                "no_identification_markings_details": "",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["identification_markings_details"], [strings.Goods.FIREARM_GOOD_NO_DETAILS_ON_MARKINGS])

    def test_add_category_two_good_yes_markings_selected_success(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "No",
                "firearms_act_section": "firearms_act_section2",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "",
                "has_identification_markings": "True",
                "identification_markings_details": "some marking details",
                "no_identification_markings_details": "",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue(good["firearm_details"]["has_identification_markings"])
        self.assertEquals(
            good["firearm_details"]["identification_markings_details"],
            data["firearm_details"]["identification_markings_details"],
        )

    def test_add_category_two_good_only_correct_markings_details_set_success(self):
        """ If details are provided for both answers, ensure that only the details for the given answer are stored. """
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "No",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "",
                "has_identification_markings": "True",
                "identification_markings_details": "some marking details",
                "no_identification_markings_details": "some non marking details",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue(good["firearm_details"]["has_identification_markings"])
        self.assertEquals(
            good["firearm_details"]["identification_markings_details"],
            data["firearm_details"]["identification_markings_details"],
        )
        self.assertIsNone(good["firearm_details"]["no_identification_markings_details"])

    def test_add_category_two_success(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section2",
                "section_certificate_number": "ABC123",
                "section_certificate_date_of_expiry": "2022-12-12",
                "has_identification_markings": "True",
                "identification_markings_details": "some marking details",
                "no_identification_markings_details": "",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)

        # good details
        self.assertEquals(good["description"], data["description"])
        self.assertEquals(good["is_good_controlled"]["key"], str(data["is_good_controlled"]))
        self.assertEquals(good["is_pv_graded"]["key"], data["is_pv_graded"])
        self.assertEquals(good["item_category"]["key"], data["item_category"])

        # good's firearm details
        self.assertEquals(good["firearm_details"]["type"]["key"], data["firearm_details"]["type"])
        self.assertEquals(good["firearm_details"]["calibre"], data["firearm_details"]["calibre"])
        self.assertEquals(
            str(good["firearm_details"]["year_of_manufacture"]), data["firearm_details"]["year_of_manufacture"]
        )
        self.assertEqual(good["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"], "Yes")
        self.assertEquals(
            good["firearm_details"]["section_certificate_number"], data["firearm_details"]["section_certificate_number"]
        )
        self.assertEquals(
            good["firearm_details"]["section_certificate_date_of_expiry"],
            data["firearm_details"]["section_certificate_date_of_expiry"],
        )
        self.assertTrue(good["firearm_details"]["has_identification_markings"])
        self.assertEquals(
            good["firearm_details"]["identification_markings_details"],
            data["firearm_details"]["identification_markings_details"],
        )
        self.assertIsNone(good["firearm_details"]["no_identification_markings_details"])

    @parameterized.expand(
        [
            ["True", "identification_markings_details", "no_identification_markings_details"],
            ["False", "no_identification_markings_details", "identification_markings_details"],
        ]
    )
    def test_add_category_two_good_has_markings_details_too_long_failure(
        self, has_identification_markings, details_field, other_details_fields
    ):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "No",
                "firearms_act_section": "firearms_act_section2",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "",
                "has_identification_markings": has_identification_markings,
                details_field: "A" * 2001,
                other_details_fields: "",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors[details_field], ["Ensure this field has no more than 2000 characters."])


class GoodsCreateControlledGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

        ControlListEntry.create("ML1b", "Info here", None)

    def test_when_creating_a_good_with_all_fields_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = True
        self.request_data["control_list_entries"] = ["ML1a"]

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_multiple_clcs_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = True
        self.request_data["control_list_entries"] = ["ML1a", "ML1b"]

        response = self.client.post(URL, self.request_data, **self.exporter_headers)
        response_data = response.json()["good"]["control_list_entries"]

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue({"rating": "ML1a", "text": get_control_list_entry("ML1a").text} in response_data)
        self.assertTrue({"rating": "ML1b", "text": get_control_list_entry("ML1b").text} in response_data)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_an_invalid_control_list_entries_then_bad_request_response_is_returned(self):
        self.request_data["is_good_controlled"] = True
        self.request_data["control_list_entries"] = ["invalid"]

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"control_list_entries": [strings.Goods.CONTROL_LIST_ENTRY_IVALID]}
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_not_controlled_then_no_control_list_entry_needed_success(self):
        self.request_data["is_good_controlled"] = False
        self.request_data["control_list_entries"] = []

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(Good.objects.all().count(), 1)


class GoodsCreatePvGradedGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

    def test_when_creating_a_good_with_a_custom_grading_then_created_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_a_grading_then_created_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["custom_grading"] = None
        self.request_data["pv_grading_details"]["grading"] = PvGrading.UK_OFFICIAL

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_a_null_grading_and_custom_grading_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["custom_grading"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"custom_grading": [strings.Goods.NO_CUSTOM_GRADING_ERROR]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_grading_and_custom_grading_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["grading"] = PvGrading.UK_OFFICIAL
        self.request_data["pv_grading_details"]["custom_grading"] = "Custom Grading"

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"custom_grading": [strings.Goods.PROVIDE_ONLY_GRADING_OR_CUSTOM_GRADING_ERROR]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_null_authority_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["issuing_authority"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"issuing_authority": ["This field may not be null."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_null_reference_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["reference"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"reference": ["This field may not be null."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_null_date_of_issue_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["date_of_issue"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"date_of_issue": ["This field may not be null."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)
