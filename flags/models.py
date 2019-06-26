import uuid

import reversion
from django.db import models

from flags.enums import FlagLevels, FlagStatuses
from teams.models import Team


@reversion.register()
class Flag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default='Untitled Flag')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    level = models.CharField(choices=FlagLevels.choices, max_length=20)
    status = models.CharField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE, max_length=20)
