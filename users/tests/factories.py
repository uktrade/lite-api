import factory

from api.organisations.tests.factories import OrganisationFactory
from users import models
from users.enums import UserType, UserStatuses
from users.models import Role, UserOrganisationRelationship


class GovUserFactory(factory.django.DjangoModelFactory):
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")

    class Meta:
        model = models.GovUser


class ExporterUserFactory(factory.django.DjangoModelFactory):
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")

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
