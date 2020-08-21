import factory
from django.utils import timezone

from api.applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from api.licences.models import Licence, GoodOnLicence


class LicenceFactory(factory.django.DjangoModelFactory):
    case = factory.SubFactory(StandardApplicationFactory)
    start_date = timezone.now().date()
    duration = 24

    class Meta:
        model = Licence


class GoodOnLicenceFactory(factory.django.DjangoModelFactory):
    good = factory.SubFactory(GoodOnApplicationFactory)
    licence = factory.SubFactory(LicenceFactory)

    class Meta:
        model = GoodOnLicence
