from datetime import timedelta
from copy import deepcopy
from unittest import mock

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
from api.organisations.enums import OrganisationDocumentType
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

    def test_firearm_number_of_items_invalid(self):
        data = good_rifle()
        data["firearm_details"]["number_of_items"] = 0
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["number_of_items"][0], "Enter the number of items")

    def test_firearm_missing_identification_markings_details(self):
        data = good_rifle()
        data["firearm_details"]["number_of_items"] = 5
        data["firearm_details"]["has_identification_markings"] = False
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @parameterized.expand([("all empty", ["", "", ""]), ("some empty", ["", "12345", ""])])
    def test_firearm_missing_serial_numbers_invalid(self, _, serial_numbers):
        data = good_rifle()
        data["firearm_details"]["number_of_items"] = 3
        data["firearm_details"]["has_identification_markings"] = True
        data["firearm_details"]["no_identification_markings_details"] = ""
        data["firearm_details"]["serial_numbers"] = serial_numbers
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = response.json()["errors"]
        self.assertEqual(response["serial_numbers"], ["Enter serial number in every row"])

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now", mock.Mock)
    def test_firearms_act_user_is_rfd(self):
        """ Test that checks that if the user organisation does not have a valid RFD then
        the firearms section act selection is required and when the user has a valid RFD then
        the firearms section act is assumed as Section5 """

        # without RFD, we need to provide the firearms act selected otherwise it is an error
        future_expiry_date = (now() + timedelta(days=365)).date().isoformat()
        data = {
            "name": "Rifle",
            "description": "Semi-automatic",
            "is_good_controlled": False,
            "is_pv_graded": GoodPvGraded.NO,
            "item_category": ItemCategory.GROUP2_FIREARMS,
            "validate_only": True,
            "firearm_details": {
                "type": FirearmGoodType.FIREARMS,
                "calibre": "12mm",
                "year_of_manufacture": "2018",
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "section_certificate_number": "Section5_reference_number",
                "section_certificate_date_of_expiry": future_expiry_date,
            },
        }
        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["firearms_act_section"][0], "Select which section the product is covered by")

        response = self.create_document_on_organisation(
            "RFD certificate", OrganisationDocumentType.REGISTERED_FIREARM_DEALER_CERTIFICATE
        )
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(self.organisation.document_on_organisations.count(), 1)

        data = deepcopy(data)
        data["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"] = ""
        response = self.client.post(URL, data, **self.exporter_headers)
        errors = response.json()["errors"]
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            errors["is_covered_by_firearm_act_section_one_two_or_five"][0],
            "Select yes if the product is covered by section 5 of the Firearms Act 1968",
        )

        data["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"] = "Yes"
        response = self.client.post(URL, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        firearm_details = response.json()["good"]["firearm_details"]
        self.assertEqual(firearm_details["firearms_act_section"], "firearms_act_section5")
