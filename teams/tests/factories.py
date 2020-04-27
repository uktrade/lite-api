import factory

from teams import models


class TeamFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")

    class Meta:
        model = models.Team
