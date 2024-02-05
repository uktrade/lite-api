import factory
from django.utils import timezone

from api.applications.enums import DefaultDuration
from api.applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from api.cases.enums import AdviceType
from api.licences.helpers import get_licence_reference_code
from api.licences.models import Licence, GoodOnLicence
from api.staticdata.decisions.models import Decision


class StandardLicenceFactory(factory.django.DjangoModelFactory):
    case = factory.SubFactory(StandardApplicationFactory)
    start_date = timezone.now().date()
    duration = DefaultDuration.PERMANENT_STANDARD.value
    hmrc_integration_sent_at = None

    @factory.post_generation
    def reference_code(self, create, extracted, **kwargs):
        if not create:
            return

        self.reference_code = get_licence_reference_code(extracted or self.case.reference_code)

    # https://factoryboy.readthedocs.io/en/latest/recipes.html#simple-many-to-many-relationship
    @factory.post_generation
    def decisions(self, create, extracted, **kwargs):
        if not create:
            return

        decisions = extracted or [Decision.objects.get(name=AdviceType.APPROVE)]
        self.decisions.add(*decisions)

    class Meta:
        model = Licence


class GoodOnLicenceFactory(factory.django.DjangoModelFactory):
    good = factory.SubFactory(GoodOnApplicationFactory)
    licence = factory.SubFactory(StandardLicenceFactory)

    class Meta:
        model = GoodOnLicence
