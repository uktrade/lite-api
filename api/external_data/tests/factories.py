import factory

from api.external_data.models import DenialEntity


class DenialEntityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DenialEntity
