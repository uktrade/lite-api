import uuid

import reversion
from django.db import models
from picklist_items.enums import PicklistType
from teams.models import Team


@reversion.register()
class PicklistItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, related_name='organisation_team', on_delete=models.CASCADE, blank=False)
    name = models.TextField(blank=False)
    text = models.TextField(blank=False, max_length=5000)
    type = models.CharField(choices=PicklistType.type, max_length=50)
    status = models.CharField(choices=PicklistType.status, default=PicklistType.ACTIVATE, max_length=50)
