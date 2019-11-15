import uuid

from django.db import models


class CaseStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(null=False, blank=False, max_length=50)
    priority = models.IntegerField(null=False, blank=False)
    is_read_only = models.BooleanField(blank=False, null=True)
