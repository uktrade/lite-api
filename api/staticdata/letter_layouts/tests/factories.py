import factory

from api.staticdata.letter_layouts.models import LetterLayout


class LetterLayoutFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LetterLayout
