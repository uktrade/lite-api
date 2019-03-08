from django.db import models
import uuid


class ControlCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)

    class Meta:
        db_table = "control_code"
