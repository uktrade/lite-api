import factory

from api.staticdata.countries.factories import CountryFactory
from api.parties.enums import SubType, PartyType
from api.parties.models import Party, PartyDocument


class PartyFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("address")
    name = factory.Faker("name")
    country = factory.SubFactory(CountryFactory)
    sub_type = SubType.OTHER
    type = PartyType.CONSIGNEE
    website = ""

    class Meta:
        model = Party


class PartyDocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartyDocument


class ConsigneeFactory(PartyFactory):
    type = PartyType.CONSIGNEE
    sub_type = SubType.GOVERNMENT


class EndUserFactory(PartyFactory):
    type = PartyType.END_USER
    sub_type = SubType.GOVERNMENT


class ThirdPartyFactory(PartyFactory):
    type = PartyType.THIRD_PARTY
    sub_type = SubType.GOVERNMENT


class UltimateEndUserFactory(PartyFactory):
    type = PartyType.ULTIMATE_END_USER
    sub_type = SubType.GOVERNMENT
