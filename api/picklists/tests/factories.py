import factory

from faker import Faker

from api.picklists.enums import PicklistType, PickListStatus
from api.picklists.models import PicklistItem
from api.teams.tests.factories import TeamFactory

faker = Faker()


class PicklistItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PicklistItem

    team = factory.SubFactory(TeamFactory)
    name = factory.LazyAttribute(lambda n: faker.word())
    text = factory.LazyAttribute(lambda n: faker.sentence())
    type = factory.fuzzy.FuzzyChoice(PicklistType.choices, getter=lambda t: t[0])
    status = PickListStatus.ACTIVE
