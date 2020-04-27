import factory

from teams.tests.factories import TeamFactory
from users import models
from users.enums import UserType


class GovUserFactory(factory.django.DjangoModelFactory):
    email = factory.Faker("email")
    first_name = factory.Faker("word")
    last_name = factory.Faker("word")
    type = UserType.INTERNAL
    team = factory.SubFactory(TeamFactory)

    class Meta:
        model = models.GovUser
