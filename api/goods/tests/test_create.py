import uuid
from copy import deepcopy
from datetime import timedelta

from django.utils.timezone import now
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
    self.assertEqual(response_data["description"], request_data["description"])
    self.assertEqual(response_data["part_number"], request_data["part_number"])
    self.assertEqual(response_data["status"]["key"], GoodStatus.DRAFT)
    self.assertEqual(response_data["item_category"]["key"], request_data["item_category"])
    self.assertEqual(response_data["is_military_use"]["key"], request_data["is_military_use"])

    if request_data["is_good_controlled"] == True:
        self.assertEqual(response_data["is_good_controlled"]["key"], "True")
        clc_entries = response_data["control_list_entries"]
        self.assertEqual(len(response_data["control_list_entries"]), 1)
        self.assertEqual(clc_entries[0]["rating"], "ML1a")
        self.assertEqual(clc_entries[0]["text"], get_control_list_entry("ML1a").text)

    if request_data["is_pv_graded"] == GoodPvGraded.YES:
        self.assertEqual(response_data["is_pv_graded"]["key"], GoodPvGraded.YES)

        response_data_pv_grading_details = response_data["pv_grading_details"]
        request_data_pv_grading_details = request_data["pv_grading_details"]

        if request_data_pv_grading_details["grading"]:
            grading_response = response_data_pv_grading_details.pop("grading")
            grading_request = request_data_pv_grading_details.pop("grading")
            self.assertEqual(grading_response["key"], grading_request)

        for key, value in request_data_pv_grading_details.items():
            self.assertEqual(response_data_pv_grading_details[key], value)


class CreateGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

    def test_when_creating_a_good_with_not_controlled_and_not_pv_graded_then_created_response_is_returned(self):
        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_pv_graded_and_controlled_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = True
        self.request_data["control_list_entries"] = ["ML1a"]
        self.request_data["is_pv_graded"] = GoodPvGraded.YES

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_pv_graded_set_to_null_then_bad_request_response_is_returned(self):
        self.request_data["is_pv_graded"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            {"is_pv_graded": ["This field may not be null."]},
        )
        self.assertEqual(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_validate_only_then_ok_response_is_returned_and_good_is_not_created(
        self,
    ):
        self.request_data["is_good_controlled"] = False
        self.request_data["is_pv_graded"] = GoodPvGraded.NO
        self.request_data["validate_only"] = True

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Good.objects.all().count(), 0)

    def test_when_creating_a_good_that_is_not_controlled_success(
        self,
    ):
        self.request_data["is_good_controlled"] = False

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_when_creating_a_good_that_is_not_controlled_multiple_clcs_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = False
        self.request_data["control_list_entries"] = ["ML1a", "ML1b"]

        response = self.client.post(URL, self.request_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        control_list_entries = response.json()["good"]["control_list_entries"]
        ratings = [item["rating"] for item in control_list_entries]
        self.assertEqual(sorted(["ML1a", "ML1b"]), sorted(ratings))
        self.assertEqual(Good.objects.all().count(), 1)

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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
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
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors["name"], ["Enter a product name"])

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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(good["description"], data["description"])
        self.assertEqual(good["status"]["key"], GoodStatus.DRAFT)
        self.assertEqual(good["item_category"]["key"], data["item_category"])
        self.assertEqual(good["is_military_use"]["key"], data["is_military_use"])
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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(good["description"], data["description"])
        self.assertEqual(good["status"]["key"], GoodStatus.DRAFT)
        self.assertEqual(good["item_category"]["key"], data["item_category"])
        self.assertEqual(good["is_military_use"]["key"], data["is_military_use"])
        self.assertEqual(good["is_component"]["key"], data["is_component"])
        self.assertTrue(good["uses_information_security"])
        self.assertEqual(good["information_security_details"], data["information_security_details"])

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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(good["description"], data["description"])
        self.assertEqual(good["status"]["key"], GoodStatus.DRAFT)
        self.assertEqual(good["item_category"]["key"], data["item_category"])
        self.assertEqual(good["software_or_technology_details"], data["software_or_technology_details"])
        self.assertEqual(good["is_military_use"]["key"], data["is_military_use"])
        self.assertTrue(good["uses_information_security"])
        self.assertEqual(good["information_security_details"], data["information_security_details"])

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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors["software_or_technology_details"], ["Ensure this field has no more than 2000 characters."]
        )

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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["type"], [strings.Goods.FIREARM_GOOD_NO_TYPE])

    @parameterized.expand([[timezone.now().date().year], [timezone.now().date().year - 1]])
    def test_add_category_two_good_no_year_of_manufacture_in_the_past_success(self, year):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "is_military_use": MilitaryUse.NO,
            "modified_military_use_details": "",
            "uses_information_security": False,
            "firearm_details": {"type": FirearmGoodType.AMMUNITION, "calibre": "0.5", "year_of_manufacture": str(year)},
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["firearm_details"]["year_of_manufacture"], year)

    def test_add_firearms_certificate_missing_checks_with_expiry(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "is_military_use": MilitaryUse.NO,
            "modified_military_use_details": "",
            "uses_information_security": False,
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["section_certificate_number"][0], "Enter the certificate number")

        data["firearm_details"]["section_certificate_number"] = "FR8C1604"
        data["firearm_details"]["section_certificate_date_of_expiry"] = None
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
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
            "is_military_use": MilitaryUse.NO,
            "modified_military_use_details": "",
            "uses_information_security": False,
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(
            response["section_certificate_missing_reason"][0],
            "Enter a reason why you do not have a section 1 certificate",
        )

        data["firearm_details"]["section_certificate_missing_reason"] = "Certificate not required"
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            errors["section_certificate_date_of_expiry"],
            ["Enter the expiry date and include a day, month and year"],
        )

    def test_add_category_two_good_certificate_details_not_set_on_no_success(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "is_military_use": MilitaryUse.NO,
            "modified_military_use_details": "",
            "uses_information_security": False,
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(good["firearm_details"]["section_certificate_date_of_expiry"])
        self.assertIsNone(good["firearm_details"]["section_certificate_number"])
        self.assertEqual(good["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"], "No")

    def test_add_category_two_good_yes_markings_selected_success(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "is_military_use": MilitaryUse.NO,
            "modified_military_use_details": "",
            "uses_information_security": False,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "No",
                "firearms_act_section": "firearms_act_section2",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "",
                "serial_numbers_available": "AVAILABLE",
                "no_identification_markings_details": "",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["firearm_details"]["serial_numbers_available"], "AVAILABLE")

    def test_add_category_two_good_only_correct_markings_details_set_success(self):
        """If details are provided for both answers, ensure that only the details for the given answer are stored."""
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "is_military_use": MilitaryUse.NO,
            "modified_military_use_details": "",
            "uses_information_security": False,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "No",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": "",
                "serial_numbers_available": "AVAILABLE",
                "no_identification_markings_details": "some non marking details",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["firearm_details"]["serial_numbers_available"], "AVAILABLE")
        self.assertIsNone(good["firearm_details"]["no_identification_markings_details"])

    def test_add_category_two_success(self):
        data = {
            "name": "Rifle",
            "description": "Firearm product",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "is_military_use": MilitaryUse.NO,
            "modified_military_use_details": "",
            "uses_information_security": False,
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "calibre": "0.5",
                "year_of_manufacture": "1991",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section2",
                "section_certificate_number": "ABC123",
                "section_certificate_date_of_expiry": (now() + timedelta(days=365)).date().isoformat(),
                "serial_numbers_available": "AVAILABLE",
                "no_identification_markings_details": "",
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # good details
        self.assertEqual(good["description"], data["description"])
        self.assertEqual(good["is_good_controlled"]["key"], str(data["is_good_controlled"]))
        self.assertEqual(good["is_pv_graded"]["key"], data["is_pv_graded"])
        self.assertEqual(good["item_category"]["key"], data["item_category"])

        # good's firearm details
        self.assertEqual(good["firearm_details"]["type"]["key"], data["firearm_details"]["type"])
        self.assertEqual(good["firearm_details"]["calibre"], data["firearm_details"]["calibre"])
        self.assertEqual(
            str(good["firearm_details"]["year_of_manufacture"]), data["firearm_details"]["year_of_manufacture"]
        )
        self.assertEqual(good["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"], "Yes")
        self.assertEqual(
            good["firearm_details"]["section_certificate_number"], data["firearm_details"]["section_certificate_number"]
        )
        self.assertEqual(
            good["firearm_details"]["section_certificate_date_of_expiry"],
            data["firearm_details"]["section_certificate_date_of_expiry"],
        )
        self.assertEqual(good["firearm_details"]["serial_numbers_available"], "AVAILABLE")
        self.assertIsNone(good["firearm_details"]["no_identification_markings_details"])

    def test_add_category_two_good_has_markings_details_too_long_failure(self):
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
                "serial_numbers_available": "NOT_AVAILABLE",
                "no_identification_markings_details": "A" * 2001,
            },
        }

        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            errors["no_identification_markings_details"], ["Ensure this field has no more than 2000 characters."]
        )

    @parameterized.expand(
        [
            ["no"],
            ["yes"],
        ]
    )
    def test_create_good_with_and_without_document(self, is_document_available):
        self.request_data["is_document_available"] = is_document_available
        response = self.client.post(URL, self.request_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEqual(Good.objects.all().count(), 1)


class GoodsCreateControlledGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

    def test_when_creating_a_good_with_all_fields_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = True
        self.request_data["control_list_entries"] = ["ML1a"]

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_multiple_clcs_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = True
        self.request_data["control_list_entries"] = ["ML1a", "ML1b"]

        response = self.client.post(URL, self.request_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()["good"]["control_list_entries"]
        self.assertEqual(len(response_data), len(self.request_data["control_list_entries"]))
        for item in response_data:
            actual_rating = item["rating"]
            self.assertTrue(actual_rating in self.request_data["control_list_entries"])
            self.assertEqual(item["text"], get_control_list_entry(actual_rating).text)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_an_invalid_control_list_entries_then_bad_request_response_is_returned(self):
        self.request_data["is_good_controlled"] = True
        self.request_data["control_list_entries"] = ["invalid"]

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"control_list_entries": [strings.Goods.CONTROL_LIST_ENTRY_IVALID]})
        self.assertEqual(Good.objects.all().count(), 0)

    def test_when_creating_a_good_not_controlled_then_no_control_list_entry_needed_success(self):
        self.request_data["is_good_controlled"] = False
        self.request_data["control_list_entries"] = []

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Good.objects.all().count(), 1)


class GoodsCreatePvGradedGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

    def test_when_creating_a_good_with_a_custom_grading_then_created_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_a_grading_then_created_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["grading"] = PvGrading.UK_OFFICIAL

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_when_creating_a_good_with_a_null_authority_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["issuing_authority"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            {"issuing_authority": ["This field may not be null."]},
        )
        self.assertEqual(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_null_reference_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["reference"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            {"reference": ["This field may not be null."]},
        )
        self.assertEqual(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_null_date_of_issue_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["date_of_issue"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            {"date_of_issue": ["This field may not be null."]},
        )
        self.assertEqual(Good.objects.all().count(), 0)
