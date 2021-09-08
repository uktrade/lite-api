import factory

from api.addresses.models import Address
from api.staticdata.countries.models import Country
from api.staticdata.countries.helpers import get_country
from api.staticdata.countries.factories import CountryFactory


def AddressFactoryGB():
    return AddressFactory(country=get_country(pk="GB"))


class AddressFactory(factory.django.DjangoModelFactory):
    address_line_1 = factory.Faker("street_address")
    address_line_2 = factory.Faker("secondary_address")
    region = factory.Faker("state")
    postcode = factory.Faker("postcode")
    city = factory.Faker("city")
    country = factory.SubFactory(CountryFactory)

    class Meta:
        model = Address


class ForeignAddressFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("address")
    country = factory.Iterator(Country.objects.all())

    class Meta:
        model = Address
