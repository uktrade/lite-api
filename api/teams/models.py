import uuid

from django.db import models


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)


class TeamManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, unique=True)
    part_of_ecju = models.BooleanField(default=None, null=True)
    department = models.ForeignKey(
        Department, null=True, blank=True, default=None, on_delete=models.SET_NULL, related_name="teams"
    )

    objects = TeamManager()

    class Meta:
        ordering = ["name"]

    def natural_key(self):
        return (self.name,)
