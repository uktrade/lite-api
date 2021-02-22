from rest_framework import status
from rest_framework.reverse import reverse

from api.goods.enums import (
    GoodPvGraded,
    ItemCategory,
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

    def test_firearm_number_of_items_invalid(self):
        data = good_rifle()
        data["firearm_details"]["number_of_items"] = 0
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["number_of_items"][0], "Enter the number of items")

    def test_firearm_missing_identification_markings_details(self):
        data = good_rifle()
        data["firearm_details"]["number_of_items"] = 5
        data["firearm_details"]["has_identification_markings"] = False
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(
            response["no_identification_markings_details"][0], "Enter a reason why the product has not been marked"
        )

    def test_firearm_with_serial_numbers_success(self):
        data = good_rifle()
        data["firearm_details"]["number_of_items"] = 3
        data["firearm_details"]["has_identification_markings"] = True
        data["firearm_details"]["no_identification_markings_details"] = ""
        data["firearm_details"]["serial_numbers"] = ["serial1", "serial2", "serial3"]
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
