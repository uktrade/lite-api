import uuid

from django.db import models

from cases.enums import CaseType


class CaseStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(null=False, blank=False, max_length=50)
    priority = models.IntegerField(null=False, blank=False)
    is_read_only = models.BooleanField(blank=False, null=True)


class CaseStatusCaseType(models.Model):
    class Meta:
        unique_together = (("type", "status"),)

    type = models.CharField(choices=CaseType.choices, null=False, max_length=35)
    status = models.ForeignKey(CaseStatus, on_delete=models.CASCADE, null=False)
