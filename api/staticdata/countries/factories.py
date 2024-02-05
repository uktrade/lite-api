import factory

from api.staticdata.countries.models import Country


class CountryFactory(factory.django.DjangoModelFactory):
    id = factory.Iterator(["IT", "ES"])
    name = factory.Iterator(["Italy", "Spain"])
    is_eu = False
    type = factory.Iterator(["1", "2", "3"])

    class Meta:
        model = Country
        django_get_or_create = ("id",)
