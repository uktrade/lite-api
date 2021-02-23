import uuid

from django.db import models


class CaseStatusManager(models.Manager):
    def get_by_natural_key(self, status):
        return self.get(status=status)


class CaseStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(null=False, blank=False, max_length=50, unique=True)
    priority = models.PositiveSmallIntegerField(null=False, blank=False)
    workflow_sequence = models.PositiveSmallIntegerField(null=True)
    is_read_only = models.BooleanField(blank=False, null=True)
    is_terminal = models.BooleanField(blank=False, null=True)

    objects = CaseStatusManager()

    def natural_key(self):
        return (self.status,)


class CaseStatusCaseType(models.Model):
    class Meta:
        unique_together = ("case_type", "status")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_type = models.ForeignKey("cases.CaseType", on_delete=models.DO_NOTHING, null=True, blank=False, default=None)
    status = models.ForeignKey(CaseStatus, on_delete=models.CASCADE, null=False)
