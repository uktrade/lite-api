import random

import factory

from api.flags import models
from api.flags.enums import FlagColours, FlagStatuses, FlagLevels


def get_flag_priority():
    return random.randint(0, 100)  # nosec


def get_flag_level():
    lt_choices = [x[0] for x in FlagLevels.choices if x[0] != FlagLevels.PARTY_ON_APPLICATION]  # nosec
    return random.choice(lt_choices)  # nosec


class FlagFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    status = FlagStatuses.ACTIVE
    level = factory.LazyFunction(get_flag_level)
    team = NotImplementedError()
    colour = FlagColours.DEFAULT
    label = None
    priority = factory.LazyFunction(get_flag_priority)

    class Meta:
        model = models.Flag
