import uuid

from django.db import models

from teams.models import Team


class Queue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default="Untitled Queue")
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    class Meta:
        ordering = ["name"]
