import random

import factory
from django.utils import timezone

from addresses.tests.factories import AddressFactory
from organisations import models
from api.organisations.enums import OrganisationType, OrganisationStatus
from api.organisations.tests.providers import OrganisationProvider

factory.Faker.add_provider(OrganisationProvider)


def get_organisation_type():
    lt_choices = [x[0] for x in OrganisationType.choices]  # nosec
    return random.choice(lt_choices)  # nosec


class OrganisationFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("company")
    type = factory.LazyFunction(get_organisation_type)
    status = OrganisationStatus.ACTIVE
    eori_number = factory.Faker("eori_number")
    sic_number = factory.Faker("sic_number")
    vat_number = factory.Faker("vat_number")
    registration_number = factory.Faker("registration_number")
    primary_site = factory.SubFactory("organisations.tests.factories.SiteFactory", organisation=None)
    created_at = factory.LazyAttribute(lambda _: timezone.now())
    updated_at = factory.LazyAttribute(lambda _: timezone.now())

    class Meta:
        model = models.Organisation


class SiteFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    organisation = factory.SubFactory(OrganisationFactory)
    address = factory.SubFactory(AddressFactory)

    class Meta:
        model = models.Site

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user_organisation_relationship in extracted:
                self.users.add(user_organisation_relationship)

    @factory.post_generation
    def site_records_located_at(self, create, extracted, **kwargs):
        self.site_records_located_at = self
        self.save()
