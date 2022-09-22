import factory

from ..models import (
    Regime,
    RegimeEntry,
    RegimeSubsection,
)


class RegimeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Regime

    name = factory.Faker("word")


class RegimeSubsectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RegimeSubsection

    name = factory.Faker("word")


class RegimeEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RegimeEntry

    name = factory.Faker("word")
