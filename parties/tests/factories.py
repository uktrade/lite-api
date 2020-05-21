import factory

from static.countries.factories import CountryFactory
from parties.enums import SubType, PartyType
from parties.models import Party


class PartyFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("address")
    name = factory.Faker("name")
    country = factory.SubFactory(CountryFactory)
    sub_type = SubType.OTHER
    type = PartyType.CONSIGNEE

    class Meta:
        model = Party
