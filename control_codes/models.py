from django.db import models
import uuid


class ControlList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True, null=True)
    friendly_name = models.TextField(default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)

    class Meta:
        db_table = "control_list"


class ControlCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)
    decontrolled = models.BooleanField(default=False)

    class Meta:
        db_table = "control_code"


class GlobalDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField()

    class Meta:
        db_table = "global_definition"


class LocalDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField()

    class Meta:
        db_table = "local_definition"
