import factory

from cases.enums import AdviceLevel, AdviceType
from cases.models import Advice, GoodCountryDecision
from goodstype.tests.factories import GoodsTypeFactory
from static.countries.factories import CountryFactory


class UserAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    level = AdviceLevel.USER

    class Meta:
        model = Advice


class TeamAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    level = AdviceLevel.TEAM

    class Meta:
        model = Advice


class FinalAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    level = AdviceLevel.FINAL

    class Meta:
        model = Advice


class GoodCountryDecisionFactory(factory.django.DjangoModelFactory):
    goods_type = factory.SubFactory(GoodsTypeFactory, application=factory.SelfAttribute("..case"))
    country = factory.SubFactory(CountryFactory)
    approve = True

    class Meta:
        model = GoodCountryDecision
