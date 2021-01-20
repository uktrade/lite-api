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
)
from api.goods.models import Good, PvGradingDetails
from api.goods.tests.factories import GoodFactory
from lite_content.lite_api import strings
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from api.staticdata.control_list_entries.models import ControlListEntry
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

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["is_good_controlled"]["key"], "False")
        self.assertEquals(response.json()["good"]["control_list_entries"], [])

        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_updating_non_clc_the_clc_is_not_overwritten(self):
        ratings = ["ML1a", "ML1b"]
        request_data = {"is_good_controlled": True, "control_list_entries": ratings}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(
            sorted(response.json()["good"]["control_list_entries"], key=lambda i: i["rating"]),
            [
                {"rating": "ML1a", "text": get_control_list_entry("ML1a").text},
                {"rating": "ML1b", "text": get_control_list_entry("ML1b").text},
            ],
        )

        request_data = {
            "is_military_use": MilitaryUse.YES_DESIGNED,
            "modified_military_use_details": "",
        }
        response = self.client.put(self.url, request_data, **self.exporter_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(
            sorted(response.json()["good"]["control_list_entries"], key=lambda i: i["rating"]),
            [
                {"rating": "ML1a", "text": get_control_list_entry("ML1a").text},
                {"rating": "ML1b", "text": get_control_list_entry("ML1b").text},
            ],
        )

    def test_when_updating_clc_control_list_entries_then_new_control_list_entries_is_returned(self):
        request_data = {"is_good_controlled": True, "control_list_entries": ["ML1a", "ML1b"]}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(
            sorted(response.json()["good"]["control_list_entries"], key=lambda i: i["rating"]),
            [
                {"rating": "ML1a", "text": get_control_list_entry("ML1a").text},
                {"rating": "ML1b", "text": get_control_list_entry("ML1b").text},
            ],
        )
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_removing_a_clc_control_list_entry_from_many_then_new_control_list_entries_is_returned(self):
        good = GoodFactory(
            organisation=self.organisation, is_good_controlled=True, control_list_entries=["ML1a", "ML1b"]
        )
        url = reverse("goods:good", kwargs={"pk": str(good.id)})

        request_data = {"is_good_controlled": True, "control_list_entries": ["ML1b"]}

        response = self.client.put(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(
            response.json()["good"]["control_list_entries"],
            [{"rating": "ML1b", "text": get_control_list_entry("ML1b").text}],
        )

    def test_when_updating_is_pv_graded_to_no_then_pv_grading_details_are_deleted(self):
        request_data = {"is_pv_graded": GoodPvGraded.NO}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["is_pv_graded"]["key"], GoodPvGraded.NO)
        self.assertEquals(response.json()["good"]["pv_grading_details"], None)
        self.assertEquals(Good.objects.all().count(), 1)
        self.assertEquals(PvGradingDetails.objects.all().count(), 0)

    def test_when_updating_pv_grading_details_then_new_details_are_returned(self):
        pv_grading_details = self.good.pv_grading_details.__dict__
        pv_grading_details.pop("_state")
        pv_grading_details.pop("id")
        pv_grading_details["grading"] = PvGrading.UK_OFFICIAL
        pv_grading_details["custom_grading"] = None
        pv_grading_details["date_of_issue"] = "2020-01-01"
        request_data = {"is_pv_graded": GoodPvGraded.YES, "pv_grading_details": pv_grading_details}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["pv_grading_details"]["date_of_issue"], "2020-01-01")
        self.assertEquals(response.json()["good"]["pv_grading_details"]["grading"]["key"], PvGrading.UK_OFFICIAL)
        self.assertEquals(response.json()["good"]["pv_grading_details"]["custom_grading"], None)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_edit_military_use_to_designed_success(self):
        request_data = {
            "is_military_use": MilitaryUse.YES_DESIGNED,
            "modified_military_use_details": "",
        }

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["is_military_use"]["key"], MilitaryUse.YES_DESIGNED)
        self.assertEqual(good["modified_military_use_details"], None)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_edit_military_use_to_modified_and_details_set_success(self):
        request_data = {"is_military_use": MilitaryUse.YES_MODIFIED, "modified_military_use_details": "some details"}

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["is_military_use"]["key"], MilitaryUse.YES_MODIFIED)
        self.assertEqual(good["modified_military_use_details"], "some details")
        self.assertEquals(Good.objects.all().count(), 1)

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

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["is_military_use"]["key"], MilitaryUse.NO)
        self.assertEqual(good["modified_military_use_details"], None)
        # 2 due to creating a new good for this test
        self.assertEquals(Good.objects.all().count(), 2)

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

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["is_component"]["key"], component)
        self.assertEquals(good["component_details"], details)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_edit_component_to_no_clears_details_field_success(self):
        good = self.create_good(
            "a good", self.organisation, is_component=Component.YES_MODIFIED, component_details="modified details"
        )

        request_data = {"is_component": Component.NO}
        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["is_component"]["key"], Component.NO)
        self.assertEquals(good["component_details"], None)
        # 2 due to creating a new good for this test
        self.assertEquals(Good.objects.all().count(), 2)

    def test_edit_information_security_to_no_clears_details_field_success(self):
        request_data = {"uses_information_security": False, "information_security_details": ""}

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(good["uses_information_security"])
        self.assertEquals(good["information_security_details"], "")
        self.assertEquals(Good.objects.all().count(), 1)

    @parameterized.expand([[True, "new details"], [True, ""]])
    def test_edit_information_security_also_edits_the_details(self, uses_information_security, details):
        request_data = {"uses_information_security": uses_information_security, "information_security_details": details}

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["uses_information_security"], uses_information_security)
        self.assertEquals(good["information_security_details"], details)
        self.assertEquals(Good.objects.all().count(), 1)

    @parameterized.expand(
        [
            [Component.YES_DESIGNED, "designed_details", strings.Goods.NO_DESIGN_COMPONENT_DETAILS],
            [Component.YES_MODIFIED, "modified_details", strings.Goods.NO_MODIFIED_COMPONENT_DETAILS],
            [Component.YES_GENERAL_PURPOSE, "general_details", strings.Goods.NO_GENERAL_COMPONENT_DETAILS],
        ]
    )
    def test_edit_component_to_yes_option_with_no_details_field_failure(self, component, details_field, error):
        good = self.create_good("a good", self.organisation, is_component=Component.NO)
        request_data = {"is_component": component, details_field: ""}
        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})

        response = self.client.put(url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEquals(errors[details_field], [error])
        self.assertEquals(good.is_component, Component.NO)
        self.assertIsNone(good.component_details)

    def test_edit_component_no_selection_failure(self):
        request_data = {"is_component_step": True}

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEquals(errors["is_component"], [strings.Goods.FORM_NO_COMPONENT_SELECTED])

    def test_edit_information_security_no_selection_failure(self):
        request_data = {"uses_information_security": ""}

        response = self.client.put(self.edit_details_url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEquals(
            errors["uses_information_security"], [strings.Goods.FORM_PRODUCT_DESIGNED_FOR_SECURITY_FEATURES]
        )

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

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["software_or_technology_details"], details)
        # 2 due to creating a new good for this test
        self.assertEquals(Good.objects.all().count(), 2)

    @parameterized.expand(
        [
            [ItemCategory.GROUP3_SOFTWARE, strings.Goods.FORM_NO_SOFTWARE_DETAILS],
            [ItemCategory.GROUP3_TECHNOLOGY, strings.Goods.FORM_NO_TECHNOLOGY_DETAILS],
        ]
    )
    def test_edit_software_or_technology_details_failure(self, category, error):
        good = self.create_good(
            "a good", self.organisation, item_category=category, software_or_technology_details="initial details"
        )
        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"is_software_or_technology_step": True, "software_or_technology_details": ""}

        response = self.client.put(url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEquals(errors["software_or_technology_details"], [error])

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

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(errors["non_field_errors"], [strings.Goods.CANNOT_SET_DETAILS_ERROR])

    def test_cannot_edit_software_technology_details_non_category_three_good_failure(self):
        good = self.create_good("a good", self.organisation, item_category=ItemCategory.GROUP1_PLATFORM)
        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"software_or_technology_details": "some details"}

        response = self.client.put(url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(errors["non_field_errors"], [strings.Goods.CANNOT_SET_DETAILS_ERROR])

    def test_edit_category_two_product_type_success(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"firearm_details": {"type": FirearmGoodType.FIREARMS}}

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        # created good is set as 'ammunition' type
        self.assertEquals(good["firearm_details"]["type"]["key"], FirearmGoodType.FIREARMS)
        # 2 due to creating a new good for this test
        self.assertEquals(Good.objects.all().count(), 2)

    def test_update_firearm_type_invalidates_notapplicable_fields(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )
        self.assertTrue(good.firearm_details.is_sporting_shotgun)

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"firearm_details": {"type": FirearmGoodType.FIREARMS_ACCESSORY}}

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["firearm_details"]["type"]["key"], FirearmGoodType.FIREARMS_ACCESSORY)
        self.assertIsNone(good["firearm_details"]["is_sporting_shotgun"])
        self.assertIsNone(good["firearm_details"]["year_of_manufacture"])
        self.assertEqual(good["firearm_details"]["calibre"], "")
        self.assertEqual(good["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"], "")
        self.assertIsNone(good["firearm_details"]["has_identification_markings"])
        # 2 due to creating a new good for this test
        self.assertEquals(Good.objects.all().count(), 2)

    def test_edit_category_two_calibre_and_year_of_manufacture_success(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {"firearm_details": {"calibre": "1.0", "year_of_manufacture": "2019"}}

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        # created good is set as 'ammunition' type
        self.assertEquals(good["firearm_details"]["calibre"], "1.0")
        self.assertEquals(good["firearm_details"]["year_of_manufacture"], 2019)
        # 2 due to creating a new good for this test
        self.assertEquals(Good.objects.all().count(), 2)

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

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["firearm_details"]["is_replica"], True)
        self.assertEquals(good["firearm_details"]["replica_description"], "Yes this is a replica")

        request_data = {"firearm_details": {"type": "firearms", "is_replica": False}}
        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(good["firearm_details"]["is_replica"], False)
        self.assertEquals(good["firearm_details"]["replica_description"], "")
        # 2 due to creating a new good for this test
        self.assertEquals(Good.objects.all().count(), 2)

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

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        # created good is set as 'ammunition' type
        self.assertTrue(good["firearm_details"]["is_covered_by_firearm_act_section_one_two_or_five"])
        self.assertEquals(good["firearm_details"]["section_certificate_number"], "ABC123")
        self.assertEquals(good["firearm_details"]["section_certificate_date_of_expiry"], future_expiry_date)
        # 2 due to creating a new good for this test
        self.assertEquals(Good.objects.all().count(), 2)

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

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(errors["section_certificate_number"], ["Enter the certificate number"])

    def test_edit_category_two_section_question_and_invalid_expiry_date_failure(self):
        """Test editing section of firearms question failure by providing an expiry date not in the future. """
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

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        # assert good didn't get edited
        self.assertEqual(good.firearm_details.is_covered_by_firearm_act_section_one_two_or_five, "No")
        self.assertIsNone(good.firearm_details.section_certificate_number)
        self.assertIsNone(good.firearm_details.section_certificate_date_of_expiry)
        self.assertEquals(
            errors["section_certificate_date_of_expiry"], [strings.Goods.FIREARM_GOOD_INVALID_EXPIRY_DATE]
        )

    def test_edit_category_two_identification_markings_details_success(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {
            "firearm_details": {
                "has_identification_markings": "True",
                "identification_markings_details": "some new details",
                "no_identification_markings_details": "",
            }
        }

        response = self.client.put(url, request_data, **self.exporter_headers)
        good = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue(good["firearm_details"]["has_identification_markings"])
        self.assertEquals(good["firearm_details"]["identification_markings_details"], "some new details")
        self.assertEquals(good["firearm_details"]["no_identification_markings_details"], "")

    def test_edit_category_two_identification_markings_no_details_provided_failure(self):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})
        request_data = {
            "firearm_details": {
                "has_identification_markings": "True",
                "identification_markings_details": "",
                "no_identification_markings_details": "",
            }
        }

        response = self.client.put(url, request_data, **self.exporter_headers)
        errors = response.json()["errors"]

        good.refresh_from_db()

        # assert good didn't get edited
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(good.firearm_details.has_identification_markings)
        self.assertEquals(good.firearm_details.identification_markings_details, "some marking details")
        self.assertEquals(good.firearm_details.no_identification_markings_details, "")
        self.assertEqual(errors["identification_markings_details"], [strings.Goods.FIREARM_GOOD_NO_DETAILS_ON_MARKINGS])

    @parameterized.expand(
        [
            ["True", "identification_markings_details", "no_identification_markings_details"],
            ["False", "no_identification_markings_details", "identification_markings_details"],
        ]
    )
    def test_edit_category_two_good_has_markings_details_too_long_failure(
        self, has_identification_markings, details_field, other_details_fields
    ):
        good = self.create_good(
            "a good", self.organisation, item_category=ItemCategory.GROUP2_FIREARMS, create_firearm_details=True
        )

        url = reverse("goods:good_details", kwargs={"pk": str(good.id)})

        data = {
            "description": "coffee",
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
                "has_identification_markings": has_identification_markings,
                details_field: "A" * 2001,
                other_details_fields: "",
            },
        }

        response = self.client.put(url, data, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(errors[details_field], ["Ensure this field has no more than 2000 characters."])
