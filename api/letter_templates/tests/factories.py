import factory

from api.cases.enums import CaseTypeEnum

from api.letter_templates.models import LetterTemplate
from api.staticdata.letter_layouts.models import LetterLayout


class LayoutFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    filename = factory.Faker("word")

    class Meta:
        model = LetterLayout


class LetterTemplateFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    layout = factory.SubFactory(LayoutFactory)
    visible_to_exporter = False
    include_digital_signature = False

    @factory.post_generation
    def case_types(self, create, extracted, **kwargs):
        if not create:
            return

        case_types = extracted or [CaseTypeEnum.SIEL.id]
        self.case_types.set(case_types)

    @factory.post_generation
    def decisions(self, create, extracted, **kwargs):
        if not create:
            return

        decisions = extracted or []
        self.decisions.set(decisions)

    class Meta:
        model = LetterTemplate


class SIELLicenceTemplateFactory(LetterTemplateFactory):
    layout_id = "00000000-0000-0000-0000-000000000001"
