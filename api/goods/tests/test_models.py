from django.forms import model_to_dict
from django.utils import timezone
from parameterized import parameterized

from api.applications.models import GoodOnApplication
from api.applications.tests.factories import (
    GoodOnApplicationFactory,
    StandardApplicationFactory,
)
from api.goods.enums import GoodStatus
from api.goods.tests.factories import FirearmFactory
from api.staticdata.control_list_entries.models import ControlListEntry
from test_helpers.clients import DataTestClient

from .factories import GoodFactory


class GoodTests(DataTestClient):

    @parameterized.expand(
        [
            GoodStatus.DRAFT,
            GoodStatus.SUBMITTED,
            GoodStatus.QUERY,
        ],
    )
    def test_get_precedents_unverified(self, good_status):
        good = GoodFactory(
            organisation=self.organisation,
            status=good_status,
        )
        good.save()

        good_on_application_with_null_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
            control_list_entries=None,
        )
        good_on_application_with_null_cles.save()
        self.assertQuerysetEqual(
            good.get_precedents(),
            GoodOnApplication.objects.none(),
        )

        good_on_application_with_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
        )
        good_on_application_with_cles.save()
        good_on_application_with_cles.control_list_entries.add(
            ControlListEntry.objects.first(),
        )
        self.assertQuerysetEqual(
            good.get_precedents(),
            GoodOnApplication.objects.none(),
        )

    def test_get_precedents_verified(self):
        good = GoodFactory(
            organisation=self.organisation,
            status=GoodStatus.VERIFIED,
        )
        good.save()

        good_on_application_with_null_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
            control_list_entries=None,
        )
        good_on_application_with_null_cles.save()
        self.assertQuerysetEqual(
            good.get_precedents(),
            GoodOnApplication.objects.none(),
        )

        good_on_application_with_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
        )
        good_on_application_with_cles.save()
        control_list_entry = ControlListEntry.objects.first()
        good_on_application_with_cles.control_list_entries.add(control_list_entry)
        self.assertQuerysetEqual(
            good.get_precedents(),
            [good_on_application_with_cles],
        )

        another_good_on_application_with_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
        )
        another_good_on_application_with_cles.save()
        control_list_entry = ControlListEntry.objects.first()
        another_good_on_application_with_cles.control_list_entries.add(control_list_entry)
        self.assertQuerysetEqual(
            good.get_precedents(),
            [good_on_application_with_cles, another_good_on_application_with_cles],
        )


class TestFirearmGoodDetails(DataTestClient):

    def test_clone(self):
        original_firearm_good_details = FirearmFactory(
            calibre="woo",
            category=["cat1"],
            date_of_deactivation=timezone.now(),
            deactivation_standard="some standard",
            deactivation_standard_other="some other standard",
            firearms_act_section="5",
            has_proof_mark=True,
            is_covered_by_firearm_act_section_one_two_or_five="yes",
            is_covered_by_firearm_act_section_one_two_or_five_explanation="some explanation",
            is_deactivated=False,
            is_deactivated_to_standard=False,
            is_made_before_1938=False,
            is_replica=False,
            no_identification_markings_details="some details",
            no_proof_mark_details="some more details",
            not_deactivated_to_standard_comments="some deactivated",
            number_of_items=5,
            replica_description="some description",
            section_certificate_date_of_expiry=timezone.now(),
            section_certificate_missing=False,
            section_certificate_missing_reason="some reason",
            section_certificate_number="section certificate number",
            serial_number="123",
            serial_numbers=["123", "456"],
            serial_numbers_available="available",
            type="ammunition",
            year_of_manufacture=2019,
        )
        cloned_firearm_good_details = original_firearm_good_details.clone()
        assert original_firearm_good_details.id != cloned_firearm_good_details.id
        assert model_to_dict(cloned_firearm_good_details) == {
            "id": cloned_firearm_good_details.id,
            "calibre": "woo",
            "category": [
                "cat1",
            ],
            "date_of_deactivation": original_firearm_good_details.date_of_deactivation,
            "deactivation_standard": "some standard",
            "deactivation_standard_other": "some other standard",
            "firearms_act_section": "5",
            "has_proof_mark": True,
            "is_covered_by_firearm_act_section_one_two_or_five": "yes",
            "is_covered_by_firearm_act_section_one_two_or_five_explanation": "some explanation",
            "is_deactivated": False,
            "is_deactivated_to_standard": False,
            "is_made_before_1938": False,
            "is_replica": False,
            "no_identification_markings_details": "some details",
            "no_proof_mark_details": "some more details",
            "not_deactivated_to_standard_comments": "some deactivated",
            "number_of_items": 5,
            "replica_description": "some description",
            "section_certificate_date_of_expiry": original_firearm_good_details.section_certificate_date_of_expiry,
            "section_certificate_missing": False,
            "section_certificate_missing_reason": "some reason",
            "section_certificate_number": "section certificate number",
            "serial_number": "123",
            "serial_numbers": ["123", "456"],
            "serial_numbers_available": "available",
            "type": "ammunition",
            "year_of_manufacture": 2019,
        }, """
        The attributes on the cloned record were not as expected. If this is the result
        of a schema migration, think carefully about whether the new fields should be
        cloned by default or not and adjust FirearmDetails.clone_* attributes accordingly.
        """
