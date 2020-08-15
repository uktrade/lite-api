import factory

from api.addresses.models import Address
from api.static.countries.models import Country


class AddressFactory(factory.django.DjangoModelFactory):
    address_line_1 = factory.Faker("street_address")
    address_line_2 = factory.Faker("secondary_address")
    region = factory.Faker("state")
    postcode = factory.Faker("postcode")
    city = factory.Faker("city")
    # This is intentional as CircleCI fails to find the Country table otherwise
    country = factory.Iterator(Country.objects.filter(id="GB"))

    class Meta:
        model = Address


class ForeignAddressFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("address")
    country = factory.Iterator(Country.objects.all())

    class Meta:
        model = Address
