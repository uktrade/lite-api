import factory
from teams.models import Team


class TeamFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")

    class Meta:
        model = Team
