import factory

from api.staticdata.countries.factories import CountryFactory
from api.parties.enums import SubType, PartyType
from api.parties.models import Party


class PartyFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("address")
    name = factory.Faker("name")
    country = factory.SubFactory(CountryFactory)
    sub_type = SubType.OTHER
    type = PartyType.CONSIGNEE

    class Meta:
        model = Party
