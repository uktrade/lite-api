import uuid

from django.db import models


class CaseStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    rank = models.IntegerField(null=False, blank=False)
