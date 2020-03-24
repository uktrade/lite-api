import factory

from addresses.models import Address, ForeignAddress
from static.countries.helpers import get_country
from static.countries.models import Country


class AddressFactory(factory.django.DjangoModelFactory):
    address_line_1 = factory.Faker("street_address")
    address_line_2 = factory.Faker("secondary_address")
    region = factory.Faker("state")
    postcode = factory.Faker("postcode")
    city = factory.Faker("city")
    # country = get_country("GB")

    class Meta:
        model = Address


class ForeignAddressFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("address")
    country = factory.Iterator(Country.objects.all())

    class Meta:
        model = ForeignAddress
