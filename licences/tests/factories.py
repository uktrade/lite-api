import factory

from applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from licences.models import Licence, GoodOnLicence


class LicenceFactory(factory.django.DjangoModelFactory):
    application = factory.SubFactory(StandardApplicationFactory)

    class Meta:
        model = Licence


class GoodOnLicenceFactory(factory.django.DjangoModelFactory):
    good = factory.SubFactory(GoodOnApplicationFactory)
    licence = factory.SubFactory(LicenceFactory)

    class Meta:
        model = GoodOnLicence
