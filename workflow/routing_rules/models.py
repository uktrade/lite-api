import uuid

from django.db import models

from cases.models import CaseType
from common.models import TimestampableModel
from flags.models import Flag
from queues.models import Queue
from static.countries.models import Country
from static.statuses.models import CaseStatus
from teams.models import Team
from users.models import GovUser


class RoutingRule(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    queue = models.ForeignKey(Queue, related_name="routing_queue", on_delete=models.DO_NOTHING,)
    status = models.ForeignKey(CaseStatus, related_name="routing_status", on_delete=models.DO_NOTHING,)
    tier = models.PositiveSmallIntegerField()  # positive whole number, that decides order routing rules are applied

    user = models.ForeignKey(GovUser, related_name="routing_users", on_delete=models.DO_NOTHING, blank=True, null=True)

    case_types = models.ManyToManyField(CaseType, related_name="routing_case_types", blank=True)
    flags = models.ManyToManyField(Flag, related_name="routing_flags", blank=True)
    country = models.ForeignKey(
        Country, related_name="routing_country", on_delete=models.DO_NOTHING, blank=True, null=True
    )

    class Meta:
        indexes = [models.Index(fields=["created_at", "tier"])]
        ordering = ["team__name", "status__workflow_sequence", "tier", "-created_at"]
