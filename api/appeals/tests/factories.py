import factory

from ..models import (
    Appeal,
    AppealDocument,
)


class AppealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Appeal

    grounds_for_appeal = factory.Faker("text")


class AppealDocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AppealDocument

    name = factory.Faker("file_name")
    s3_key = factory.Faker("file_name")
    safe = True
    size = factory.Faker("random_number")
