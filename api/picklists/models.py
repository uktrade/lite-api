import uuid

from django.db import models

from api.common.models import TimestampableModel
from api.picklists.enums import PicklistType, PickListStatus
from api.teams.models import Team


class PicklistItem(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, related_name="organisation_team", on_delete=models.CASCADE, blank=False)
    name = models.TextField(blank=False)
    text = models.TextField(blank=False, max_length=5000)
    type = models.CharField(choices=PicklistType.choices, max_length=50, null=False, blank=False)
    status = models.CharField(choices=PickListStatus.choices, default=PickListStatus.ACTIVE, max_length=50)

    class Meta:
        ordering: ["-updated_at"]
