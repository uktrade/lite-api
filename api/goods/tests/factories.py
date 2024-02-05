import factory
from django.utils import timezone

from api.goods import models
from api.goods.enums import ItemCategory, Component, MilitaryUse, FirearmGoodType, GoodPvGraded
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from api.staticdata.control_list_entries.models import ControlListEntry


class FirearmFactory(factory.django.DjangoModelFactory):
    type = FirearmGoodType.AMMUNITION
    category = []
    year_of_manufacture = 2019
    calibre = "5.56x45mm"
    is_covered_by_firearm_act_section_one_two_or_five = "Yes"
    section_certificate_number = "section certificate number?"
    section_certificate_date_of_expiry = factory.LazyFunction(timezone.now().date)
    serial_numbers_available = models.FirearmGoodDetails.SerialNumberAvailability.AVAILABLE
    no_identification_markings_details = ""

    class Meta:
        model = models.FirearmGoodDetails


class PvGradingDetailsFactory(factory.django.DjangoModelFactory):
    grading = None
    custom_grading = "Custom grading"
    prefix = "Prefix"
    suffix = "Suffix"
    issuing_authority = "Government organisation"
    reference = "reference"
    date_of_issue = "2024-01-01"

    class Meta:
        model = models.PvGradingDetails


class GoodFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    description = factory.Faker("word")
    is_good_controlled = False
    part_number = factory.Faker("ean13")
    organisation = None
    item_category = ItemCategory.GROUP2_FIREARMS
    firearm_details = factory.SubFactory(FirearmFactory)
    pv_grading_details = factory.SubFactory(PvGradingDetailsFactory)
    is_military_use = MilitaryUse.NO
    is_component = Component.NO
    is_pv_graded = GoodPvGraded.NO
    is_document_available = True
    is_document_sensitive = False
    uses_information_security = False
    information_security_details = None
    modified_military_use_details = None
    component_details = None
    report_summary_prefix = None
    report_summary_subject = None
    report_summary = None
    comment = None

    class Meta:
        model = models.Good

    @factory.post_generation
    def control_list_entries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if self.is_good_controlled:
            control_list_entries = extracted or ["ML1a"]
            self.control_list_entries.add(
                *list(ControlListEntry.objects.filter(rating__in=control_list_entries)),
            )

    @factory.post_generation
    def flags(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing.
            return

        self.flags.set(extracted)

    @factory.post_generation
    def pv_grading_details(self, create, extracted, **kwargs):
        if not create:
            return

        if self.is_pv_graded == GoodPvGraded.NO:
            self.pv_grading_details = None
