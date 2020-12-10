import uuid

from django.db import models

from api.teams.models import Team


class Queue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default="Untitled Queue")
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    countersigning_queue = models.ForeignKey("self", on_delete=models.DO_NOTHING, null=True)

    class Meta:
        ordering = ["name"]
        db_table = "queue"
        unique_together = ["name", "team"]
