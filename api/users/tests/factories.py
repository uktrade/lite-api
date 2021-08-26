import factory

from api.organisations.tests.factories import OrganisationFactory
from api.users import models
from api.users.enums import UserType, UserStatuses
from api.users.models import Role, UserOrganisationRelationship
from api.teams.tests.factories import TeamFactory


class BaseUserFactory(factory.django.DjangoModelFactory):
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")

    class Meta:
        model = models.BaseUser


class GovUserFactory(factory.django.DjangoModelFactory):
    baseuser_ptr = factory.SubFactory(BaseUserFactory, type=UserType.INTERNAL)
    team = factory.SubFactory(TeamFactory)

    class Meta:
        model = models.GovUser


class ExporterUserFactory(factory.django.DjangoModelFactory):
    baseuser_ptr = factory.SubFactory(BaseUserFactory, type=UserType.EXPORTER)

    class Meta:
        model = models.ExporterUser


class RoleFactory(factory.django.DjangoModelFactory):
    name = "fake_role"
    type = UserType.EXPORTER
    organisation = factory.SubFactory(OrganisationFactory)

    class Meta:
        model = Role

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for permission in extracted:
                self.permissions.add(permission)

    @factory.post_generation
    def statuses(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for status in extracted:
                self.statuses.add(status)


class UserOrganisationRelationshipFactory(factory.django.DjangoModelFactory):
    organisation = factory.SubFactory(OrganisationFactory)
    role = factory.SubFactory(RoleFactory)
    status = UserStatuses.ACTIVE

    class Meta:
        model = UserOrganisationRelationship
