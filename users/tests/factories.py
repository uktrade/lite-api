import factory

from users import models


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


