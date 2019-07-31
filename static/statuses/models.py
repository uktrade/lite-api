import uuid
from django.db import models


class CaseStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=50, blank=False, null=False, unique=True)
    priority = models.IntegerField(null=False, blank=False)
