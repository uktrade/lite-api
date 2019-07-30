import uuid

from django.db import models
from static.statuses.enums import CaseStatusEnum


class CaseStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(choices=CaseStatusEnum.choices, default=CaseStatusEnum.SUBMITTED, max_length=50)
    priority = models.IntegerField(null=False, blank=False)
