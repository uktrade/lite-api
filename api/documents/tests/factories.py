import factory

from .. import models


class DocumentFactory(factory.django.DjangoModelFactory):
    s3_key = factory.Faker("file_name", category="office")

    class Meta:
        model = models.Document
