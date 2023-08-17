import factory

from .models import Appeal


class AppealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Appeal
