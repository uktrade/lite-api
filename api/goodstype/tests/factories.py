import factory

from api.goodstype import models
from api.staticdata.control_list_entries.helpers import get_control_list_entry


class GoodsTypeFactory(factory.django.DjangoModelFactory):
    description = factory.Faker("word")
    is_good_incorporated = True
    application = None
    is_good_controlled = False

    class Meta:
        model = models.GoodsType

    @factory.post_generation
    def control_list_entries(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        # Use provided control list entries or generate one if the good is controlled
        if self.is_good_controlled:
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
