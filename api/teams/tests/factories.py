import factory

from faker import Faker

from api.teams.models import Team, Department

faker = Faker()


class DepartmentFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda _: faker.unique.name())

    class Meta:
        model = Department


class TeamFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda _: faker.unique.name())
    department = factory.SubFactory(DepartmentFactory)

    class Meta:
        model = Team
