import factory
from api.teams.models import Team, Department


class TeamFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")

    class Meta:
        model = Team


class DepartmentFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")

    class Meta:
        model = Department
