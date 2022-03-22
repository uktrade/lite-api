from datetime import timedelta

from django.utils.timezone import now
from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from api.goods.enums import (
    GoodPvGraded,
    ItemCategory,
    MilitaryUse,
    FirearmGoodType,
)
from test_helpers.clients import DataTestClient

URL = reverse("goods:goods")


def good_template():
    return {
        "name": "Rifle",
        "description": "Firearm product",
        "is_good_controlled": False,
        "is_pv_graded": GoodPvGraded.NO,
        "item_category": ItemCategory.GROUP2_FIREARMS,
        "validate_only": False,
        "is_military_use": MilitaryUse.NO,
        "modified_military_use_details": "",
        "uses_information_security": False,
        "firearm_details": {
            "type": FirearmGoodType.FIREARMS,
            "calibre": "0.5",
            "year_of_manufacture": "1991",
            "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
            "firearms_act_section": "firearms_act_section1",
            "section_certificate_missing": True,
            "section_certificate_missing_reason": "certificate not available",
        },
    }


def good_rifle():
    return {**good_template()}


class CreateFirearmGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()

    def create_document_on_organisation(self, name, document_type):
        url = reverse("organisations:documents", kwargs={"pk": self.organisation.pk})
        data = {
            "document": {"name": name, "s3_key": name, "size": 476},
            "expiry_date": (now() + timedelta(days=365)).date().isoformat(),
            "reference_code": "123",
            "document_type": document_type,
        }
        return self.client.post(url, data, **self.exporter_headers)

    def test_firearm_with_serial_numbers_success(self):
        data = good_rifle()
        data["firearm_details"]["number_of_items"] = 3
        data["firearm_details"]["serial_numbers_available"] = "AVAILABLE"
        data["firearm_details"]["no_identification_markings_details"] = ""
        data["firearm_details"]["serial_numbers"] = ["serial1", "serial2", "serial3"]
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @parameterized.expand(
        [
            (["12345", "", ""],),
            (["", "12345", ""],),
            (["", "", "12345"],),
            (["12345", "", "12345"],),
            (["12345", "12345", ""],),
            (["", "12345", "12345"],),
        ]
    )
    def test_firearm_some_missing_serial_numbers_success(self, serial_numbers):
        data = good_rifle()
        data["firearm_details"]["number_of_items"] = 3
        data["firearm_details"]["serial_numbers_available"] = "AVAILABLE"
        data["firearm_details"]["no_identification_markings_details"] = ""
        data["firearm_details"]["serial_numbers"] = serial_numbers
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_firearm_missing_serial_numbers_no_identification_valid(self):
        data = good_rifle()
        data["firearm_details"]["number_of_items"] = 3
        data["firearm_details"]["serial_numbers_available"] = "NOT_AVAILABLE"
        data["firearm_details"]["no_identification_markings_details"] = "No Serial no"
        data["firearm_details"]["serial_numbers"] = ["", "", ""]
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
