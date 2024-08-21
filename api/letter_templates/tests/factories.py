import factory

from api.letter_templates.models import LetterTemplate


class LetterTemplateFactory(factory.django.DjangoModelFactory):
    include_digital_signature = False
    visible_to_exporter = True

    class Meta:
        model = LetterTemplate
