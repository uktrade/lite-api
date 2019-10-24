import uuid

from django.db import models

from static.statuses.enums import CaseStatusEnum


class CaseStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(choices=CaseStatusEnum.choices, null=False, blank=False, max_length=50)
    priority = models.IntegerField(choices=CaseStatusEnum.priorities.items(), null=False, blank=False)

    class Meta:
        unique_together = ('status', 'priority',)
