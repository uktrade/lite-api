import factory

from api.external_data.models import Denial


class DenialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Denial
