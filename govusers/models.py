import uuid

from django.db import models

from govusers.enums import GovUserStatus
from teams.models import Team


class GovUser(models.Model):
    ACTIVE = 'active'
    DEACTIVATED = 'deactivated'
    GOV_USER_STATUS = [
        (ACTIVE, 'Active'),
        (DEACTIVATED, 'Deactivated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(choices=GovUserStatus.choices, default=GovUserStatus.ACTIVE, max_length=20)
    email = models.EmailField(default=None, blank=True, unique=True)
    team = models.ForeignKey(Team, related_name='team', on_delete=models.PROTECT)
