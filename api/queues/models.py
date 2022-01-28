import uuid

from django.db import models

from api.teams.models import Team


class QueueManager(models.Manager):
    def get_by_natural_key(self, name, team_name):
        return self.get(name=name, team__name=team_name)


class Queue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default="Untitled Queue")
    alias = models.TextField(default="", unique=True, help_text="fixed static field for reference")
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    countersigning_queue = models.ForeignKey("self", on_delete=models.DO_NOTHING, null=True)

    objects = QueueManager()

    class Meta:
        ordering = ["name"]
        db_table = "queue"
        unique_together = ["name", "team"]

    def natural_key(self):
        return (self.name, self.team.name)

    natural_key.dependencies = ["teams.Team"]
