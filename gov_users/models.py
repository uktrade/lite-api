import uuid

import reversion
from django.db import models

from gov_users.enums import GovUserStatuses
from teams.models import Team


@reversion.register()
class GovUser(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(choices=GovUserStatuses.choices, default=GovUserStatuses.ACTIVE, max_length=20)
    first_name = models.CharField(default=None, blank=True, null=True, max_length=30)
    last_name = models.CharField(default=None, blank=True, null=True, max_length=30)
    email = models.EmailField(default=None, blank=False, unique=True)
    team = models.ForeignKey(Team, related_name='team', on_delete=models.PROTECT)
