import uuid

from django.db import models


class DenialReason(models.Model):
    id = models.TextField(primary_key=True, editable=False)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False, unique=True)
    deprecated = models.BooleanField(default=False, null=False, blank=False)
    description = models.TextField(default="")
    display_value = models.TextField(default="")

    class Meta:
        ordering = ["id"]
