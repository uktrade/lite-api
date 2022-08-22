import factory
from api.teams.models import Team, Department


class DepartmentFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")

    class Meta:
        model = Department


class TeamFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    department = factory.SubFactory(DepartmentFactory)

    class Meta:
        model = Team
