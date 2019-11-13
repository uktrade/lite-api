import uuid

import reversion
from django.db import models

from picklists.enums import PicklistType, PickListStatus
from teams.models import Team


@reversion.register()
class PicklistItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team, related_name="organisation_team", on_delete=models.CASCADE, blank=False
    )
    name = models.TextField(blank=False)
    text = models.TextField(blank=False, max_length=5000)
    type = models.CharField(choices=PicklistType.choices, max_length=50)
    status = models.CharField(
        choices=PickListStatus.choices, default=PickListStatus.ACTIVE, max_length=50
    )
    last_modified_at = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        ordering: ["-last_modified_at"]
