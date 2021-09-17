import uuid

from django.db import models


class TeamManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

    def get_queryset(self):
        return super().get_queryset().exclude(is_department=True)


class TeamAndDepartmentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, unique=True)
    part_of_ecju = models.BooleanField(default=None, null=True)
    parent = models.ForeignKey("self", default=None, null=True, on_delete=models.SET_NULL)
    is_department = models.BooleanField(default=False)

    objects = TeamManager()
    teams_and_departments = TeamAndDepartmentManager()

    class Meta:
        ordering = ["name"]

    def natural_key(self):
        return (self.name,)
