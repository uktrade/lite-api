from datetime import timedelta

from django.utils.timezone import now
from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from api.goods.enums import (
    GoodPvGraded,
    PvGrading,
    MilitaryUse,
    Component,
    ItemCategory,
    FirearmGoodType,
    FirearmCategory,
)
from api.goods.models import Good, PvGradingDetails
from api.goods.tests.factories import GoodFactory
from lite_content.lite_api import strings
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from test_helpers.clients import DataTestClient


class GoodsEditDraftGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.good = self.create_good(description="This is a good", organisation=self.organisation)
        self.url = reverse("goods:good", kwargs={"pk": str(self.good.id)})
        self.edit_details_url = reverse("goods:good_details", kwargs={"pk": str(self.good.id)})

    def test_when_updating_is_good_controlled_to_no_then_control_list_entries_is_deleted(self):
        request_data = {"is_good_controlled": False}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["good"]["is_good_controlled"]["key"], "False")
        self.assertEqual(response.json()["good"]["control_list_entries"], [])

        self.assertEqual(Good.objects.all().count(), 1)

    def test_when_updating_non_clc_the_clc_is_not_overwritten(self):
        ratings = ["ML1a", "ML1b"]
        request_data = {"is_good_controlled": True, "control_list_entries": ratings}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        clc_entries = response.json()["good"]["control_list_entries"]
        self.assertEqual(len(clc_entries), len(ratings))
        for item in clc_entries:
            actual_rating = item["rating"]
            self.assertTrue(actual_rating in ratings)
            self.assertEqual(item["text"], get_control_list_entry(actual_rating).text)

        request_data = {
            "is_military_use": MilitaryUse.YES_DESIGNED,
            "modified_military_use_details": "",
        }
        response = self.client.put(self.url, request_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        clc_entries = response.json()["good"]["control_list_entries"]
        self.assertEqual(len(clc_entries), len(ratings))
        for item in clc_entries:
            actual_rating = item["rating"]
            self.assertTrue(actual_rating in ratings)
            self.assertEqual(item["text"], get_control_list_entry(actual_rating).text)

    def test_when_updating_clc_control_list_entries_then_new_control_list_entries_is_returned(self):
        ratings = ["ML1a", "ML1b"]
        request_data = {"is_good_controlled": True, "control_list_entries": ratings}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        clc_entries = response.json()["good"]["control_list_entries"]
        self.assertEqual(len(clc_entries), len(ratings))
        for item in clc_entries:
            actual_rating = item["rating"]
            self.assertTrue(actual_rating in ratings)
            self.assertEqual(item["text"], get_control_list_entry(actual_rating).text)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_when_removing_a_clc_control_list_entry_from_many_then_new_control_list_entries_is_returned(self):
        ratings = ["ML1a", "ML1b"]
        good = GoodFactory(organisation=self.organisation, is_good_controlled=True, control_list_entries=ratings)
        url = reverse("goods:good", kwargs={"pk": str(good.id)})

        request_data = {"is_good_controlled": True, "control_list_entries": ["ML1b"]}

        response = self.client.put(url, request_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        clc_entries = response.json()["good"]["control_list_entries"]
        self.assertEqual(len(clc_entries), 1)
        expected_rating = request_data["control_list_entries"][0]
        self.assertEqual(clc_entries[0]["rating"], expected_rating)
        self.assertEqual(clc_entries[0]["text"], get_control_list_entry(expected_rating).text)

    def test_when_updating_is_pv_graded_to_no_then_pv_grading_details_are_deleted(self):
        request_data = {"is_pv_graded": GoodPvGraded.NO}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["good"]["is_pv_graded"]["key"], GoodPvGraded.NO)
        self.assertEqual(response.json()["good"]["pv_grading_details"], None)
        self.assertEqual(Good.objects.all().count(), 1)
        self.assertEqual(PvGradingDetails.objects.all().count(), 0)

    def test_when_updating_pv_grading_details_then_new_details_are_returned(self):
        pv_grading_details = self.good.pv_grading_details.__dict__
        pv_grading_details.pop("_state")
        pv_grading_details.pop("id")
        pv_grading_details["grading"] = PvGrading.UK_OFFICIAL
        pv_grading_details["date_of_issue"] = "2020-01-01"
        request_data = {"is_pv_graded": GoodPvGraded.YES, "pv_grading_details": pv_grading_details}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["good"]["pv_grading_details"]["date_of_issue"], "2020-01-01")
        self.assertEqual(response.json()["good"]["pv_grading_details"]["grading"]["key"], PvGrading.UK_OFFICIAL)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_edit_military_use_to_designed_success(self):
        request_data = {
            "is_military_use": MilitaryUse.YES_DESIGNED,
            "modified_military_use_details": "",
        }

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["is_military_use"]["key"], MilitaryUse.YES_DESIGNED)
        self.assertEqual(good["modified_military_use_details"], None)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_edit_military_use_to_modified_and_details_set_success(self):
        request_data = {"is_military_use": MilitaryUse.YES_MODIFIED, "modified_military_use_details": "some details"}

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["is_military_use"]["key"], MilitaryUse.YES_MODIFIED)
        self.assertEqual(good["modified_military_use_details"], "some details")
        self.assertEqual(Good.objects.all().count(), 1)

    def test_edit_military_use_to_selection_without_details_clears_the_field_success(self):
        good = self.create_good(
            "a good",
            self.organisation,
            is_military_use=MilitaryUse.YES_MODIFIED,
            modified_military_use_details="modified details",
        )

        request_data = {"is_military_use": MilitaryUse.NO, "modified_military_use_details": ""}
        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["is_military_use"]["key"], MilitaryUse.NO)
        self.assertEqual(good["modified_military_use_details"], None)
        # 2 due to creating a new good for this test
        self.assertEqual(Good.objects.all().count(), 2)

    @parameterized.expand(
        [
            [Component.YES_MODIFIED, "modified_details", "modified details"],
            [Component.YES_DESIGNED, "designed_details", "designed details"],
            [Component.YES_GENERAL_PURPOSE, "general_details", "general details"],
        ]
    )
    def test_edit_component_to_yes_selection_with_details_success(self, component, details_field, details):
        request_data = {"is_component": component, details_field: details}

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["is_component"]["key"], component)
        self.assertEqual(good["component_details"], details)
        self.assertEqual(Good.objects.all().count(), 1)

    def test_edit_component_to_no_clears_details_field_success(self):
        good = self.create_good(
            "a good", self.organisation, is_component=Component.YES_MODIFIED, component_details="modified details"
        )

        request_data = {"is_component": Component.NO}
        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["is_component"]["key"], Component.NO)
        self.assertEqual(good["component_details"], None)
        # 2 due to creating a new good for this test
        self.assertEqual(Good.objects.all().count(), 2)

    def test_edit_information_security_to_no_clears_details_field_success(self):
        request_data = {"uses_information_security": False, "information_security_details": ""}

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(good["uses_information_security"])
        self.assertEqual(good["information_security_details"], "")
        self.assertEqual(Good.objects.all().count(), 1)

    @parameterized.expand([[True, "new details"], [True, ""]])
    def test_edit_information_security_also_edits_the_details(self, uses_information_security, details):
        request_data = {"uses_information_security": uses_information_security, "information_security_details": details}

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["uses_information_security"], uses_information_security)
        self.assertEqual(good["information_security_details"], details)
        self.assertEqual(Good.objects.all().count(), 1)

    @parameterized.expand(
        [
            [ItemCategory.GROUP3_SOFTWARE, "new software details"],
            [ItemCategory.GROUP3_TECHNOLOGY, "new technology details"],
        ]
    )
    def test_edit_software_or_technology_details_success(self, category, details):
        good = self.create_good(
            "a good", self.organisation, item_category=category, software_or_technology_details="initial details"
        )
        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"is_software_or_technology_step": True, "software_or_technology_details": details}

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["software_or_technology_details"], details)
        # 2 due to creating a new good for this test
        self.assertEqual(Good.objects.all().count(), 2)

    def test_cannot_edit_component_and_component_details_of_non_category_one_good_failure(self):
        good = self.create_good(
            "a good",
            self.organisation,
            item_category=ItemCategory.GROUP3_TECHNOLOGY,
            software_or_technology_details="initial details",
        )
        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {
            "is_component_step": True,
            "is_component": Component.YES_GENERAL_PURPOSE,
            "general_details": "some details",
        }

        response = self.client.put(url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["non_field_errors"], [strings.Goods.CANNOT_SET_DETAILS_ERROR])

    def test_cannot_edit_software_technology_details_non_category_three_good_failure(self):
        good = self.create_good("a good", self.organisation, item_category=ItemCategory.GROUP1_PLATFORM)
        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"software_or_technology_details": "some details"}

        response = self.client.put(url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["non_field_errors"], [strings.Goods.CANNOT_SET_DETAILS_ERROR])

    def test_edit_category_two_product_type_success(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"firearm_details": {"type": FirearmGoodType.FIREARMS}}

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # created good is set as 'ammunition' type
        self.assertEqual(good["firearm_details"]["type"]["key"], FirearmGoodType.FIREARMS)
        # 2 due to creating a new good for this test
        self.assertEqual(Good.objects.all().count(), 2)

    def test_edit_category_two_product_category_success(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        expected = [FirearmCategory.NON_AUTOMATIC_SHOTGUN, FirearmCategory.NON_AUTOMATIC_RIM_FIRED_RIFLE]
        request_data = {"firearm_details": {"category": expected}}

        response = self.client.put(url, request_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        firearm_details = response.json()["good"]["firearm_details"]
        actual = [category["key"] for category in firearm_details["category"]]
        self.assertEqual(actual, expected)

    def test_update_firearm_type_invalidates_notapplicable_fields(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"firearm_details": {"type": FirearmGoodType.FIREARMS_ACCESSORY}}

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["firearm_details"]["type"]["key"], FirearmGoodType.FIREARMS_ACCESSORY)
        self.assertIsNone(good["firearm_details"]["year_of_manufacture"])
        self.assertEqual(good["firearm_details"]["calibre"], "")
        self.assertEqual(good["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"], "")
        self.assertEqual(good["firearm_details"]["serial_numbers_available"], "")
        # 2 due to creating a new good for this test
        self.assertEqual(Good.objects.all().count(), 2)

    def test_edit_category_two_calibre_and_year_of_manufacture_success(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"firearm_details": {"calibre": "1.0", "year_of_manufacture": "2019"}}

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # created good is set as 'ammunition' type
        self.assertEqual(good["firearm_details"]["calibre"], "1.0")
        self.assertEqual(good["firearm_details"]["year_of_manufacture"], 2019)
        # 2 due to creating a new good for this test
        self.assertEqual(Good.objects.all().count(), 2)

    def test_edit_category_two_firearm_replica(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {
            "firearm_details": {"type": "firearms", "is_replica": True, "replica_description": "Yes this is a replica"}
        }
        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["firearm_details"]["is_replica"], True)
        self.assertEqual(good["firearm_details"]["replica_description"], "Yes this is a replica")

        request_data = {"firearm_details": {"type": "firearms", "is_replica": False}}
        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["firearm_details"]["is_replica"], False)
        self.assertEqual(good["firearm_details"]["replica_description"], "")
        # 2 due to creating a new good for this test
        self.assertEqual(Good.objects.all().count(), 2)

    def test_edit_category_two_section_question_and_details_success(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        future_expiry_date = (now() + timedelta(days=365)).date().isoformat()
        request_data = {
            "firearm_details": {
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "ABC123",
                "section_certificate_date_of_expiry": future_expiry_date,
            }
        }

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # created good is set as 'ammunition' type
        self.assertTrue(good["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"])
        self.assertEqual(good["firearm_details"]["section_certificate_number"], "ABC123")
        self.assertEqual(good["firearm_details"]["section_certificate_date_of_expiry"], future_expiry_date)
        # 2 due to creating a new good for this test
        self.assertEqual(Good.objects.all().count(), 2)

    def test_edit_category_two_section_question_and_no_certificate_number_failure(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section2",
                "section_certificate_number": "",
                "section_certificate_date_of_expiry": None,
            }
        }

        response = self.client.put(url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors["section_certificate_number"], ["Enter the certificate number"])

    def test_edit_category_two_section_question_and_invalid_expiry_date_failure(self):
        """Test editing section of firearms question failure by providing an expiry date not in the future."""
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {
            "firearm_details": {
                "type": FirearmGoodType.AMMUNITION,
                "is_covered_by_firearm_act_section_one_two_or_five": "Yes",
                "firearms_act_section": "firearms_act_section1",
                "section_certificate_number": "ABC123",
                "section_certificate_date_of_expiry": "2019-12-12",
            }
        }

        response = self.client.put(url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        good.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # assert good didn't get edited
        self.assertEqual(good.firearm_details.is_covered_by_firearm_act_section_one_two_or_five, "No")
        self.assertIsNone(good.firearm_details.section_certificate_number)
        self.assertIsNone(good.firearm_details.section_certificate_date_of_expiry)
        self.assertEqual(errors["section_certificate_date_of_expiry"], [strings.Goods.FIREARM_GOOD_INVALID_EXPIRY_DATE])

    def test_edit_category_two_identification_markings_details_success(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {
            "firearm_details": {
                "serial_numbers_available": "AVAILABLE",
                "no_identification_markings_details": "",
            }
        }

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(good["firearm_details"]["serial_numbers_available"], "AVAILABLE")
        self.assertEqual(good["firearm_details"]["no_identification_markings_details"], "")
