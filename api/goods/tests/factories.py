import factory
from django.utils import timezone

from api.goods import models
from api.goods.enums import ItemCategory, Component, MilitaryUse, FirearmGoodType, GoodPvGraded
from api.staticdata.control_list_entries.helpers import get_control_list_entry


class GoodFactory(factory.django.DjangoModelFactory):
    description = factory.Faker("word")
    is_good_controlled = False
    part_number = factory.Faker("ean13")
    organisation = None
    item_category = ItemCategory.GROUP1_COMPONENTS
    is_military_use = MilitaryUse.NO
    is_component = Component.NO
    is_pv_graded = GoodPvGraded.NO
    uses_information_security = False
    information_security_details = None
    modified_military_use_details = None
    component_details = None

    class Meta:
        model = models.Good

    @factory.post_generation
    def control_list_entries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        control_list_entries = extracted or ["ML1a", "ML2a"]
        for control_list_entry in control_list_entries:
            self.control_list_entries.add(get_control_list_entry(control_list_entry))

    @factory.post_generation
    def flags(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing.
            return

        self.flags.set(extracted)


class FirearmFactory(factory.django.DjangoModelFactory):
    type = FirearmGoodType.AMMUNITION
    year_of_manufacture = 2019
    calibre = "5.56x45mm"
    is_covered_by_firearm_act_section_one_two_or_five = True
    section_certificate_number = "section certificate number?"
    section_certificate_date_of_expiry = factory.LazyFunction(timezone.now().date)
    has_identification_markings = True
    identification_markings_details = factory.Faker("word")

    class Meta:
        model = models.FirearmGoodDetails
