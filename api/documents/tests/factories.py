import factory

from .. import models


class DocumentFactory(factory.django.DjangoModelFactory):
    safe = None
    virus_scanned_at = None
    s3_key = factory.Faker("file_name", category="office")

    class Meta:
        model = models.Document
