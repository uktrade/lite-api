import factory

from goodstype import models


class GoodsTypeFactory(factory.django.DjangoModelFactory):
    description = factory.Faker("word")
    is_good_incorporated = True
    application = None
    is_good_controlled = False

    class Meta:
        model = models.GoodsType
