import factory

from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.tests.factories import CaseSIELFactory


class GeneratedCaseDocumentFactory(factory.django.DjangoModelFactory):
    case = factory.SubFactory(CaseSIELFactory)
    name = factory.Faker("word")
    s3_key = factory.Faker("slug")
    safe = True
    visible_to_exporter = False

    class Meta:
        model = GeneratedCaseDocument
