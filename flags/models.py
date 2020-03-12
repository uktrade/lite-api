import uuid

from django.db import models

from common.models import TimestampableModel
from flags.enums import FlagLevels, FlagStatuses
from teams.models import Team


class Flag(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(default="Untitled Flag", unique=True, max_length=25)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    level = models.CharField(choices=FlagLevels.choices, max_length=20)
    status = models.CharField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE, max_length=20)


class FlaggingRule(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    level = models.CharField(choices=FlagLevels.choices, max_length=20)
    status = models.CharField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE, max_length=20)
    flag = models.ForeignKey(Flag, on_delete=models.CASCADE)
    matching_value = models.CharField(max_length=100)
