import factory

from api.cases.enums import AdviceType
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.tests.factories import CaseSIELFactory
from api.letter_templates.tests.factories import SIELLicenceTemplateFactory


class GeneratedCaseDocumentFactory(factory.django.DjangoModelFactory):
    case = factory.SubFactory(CaseSIELFactory)
    name = factory.Faker("word")
    s3_key = factory.Faker("slug")
    safe = True
    visible_to_exporter = False

    class Meta:
        model = GeneratedCaseDocument


class SIELLicenceDocumentFactory(GeneratedCaseDocumentFactory):
    text = factory.Faker("sentence")
    template = factory.SubFactory(SIELLicenceTemplateFactory)
    licence = None
    advice_type = AdviceType.APPROVE
