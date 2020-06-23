import factory

from goods import models
from goods.enums import GoodControlled, ItemCategory, Component, MilitaryUse
from static.control_list_entries.helpers import get_control_list_entry


class GoodFactory(factory.django.DjangoModelFactory):
    description = factory.Faker("word")
    is_good_controlled = GoodControlled.NO
    part_number = factory.Faker("ean13")
    organisation = None
    item_category = ItemCategory.GROUP1_COMPONENTS
    is_military_use = MilitaryUse.NO
    is_component = Component.NO
    uses_information_security = True
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

        # Use provided control list entries or generate one if the good is controlled
        if self.is_good_controlled == GoodControlled.YES:
            if not extracted:
                extracted = ["ML1a"]

            for control_list_entry in extracted:
                self.control_list_entries.add(get_control_list_entry(control_list_entry))

    @factory.post_generation
    def flags(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing.
            return

        self.flags.set(extracted)
