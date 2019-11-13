from django.db import models

from static.statuses.enums import CaseStatusEnum


class CaseStatus(models.Model):
    status = models.CharField(primary_key=True, null=False, blank=False, max_length=50)
    display_value = models.CharField(null=True, blank=False, max_length=50)
    priority = models.IntegerField(choices=CaseStatusEnum.priority.items(), null=False, blank=False)
    is_read_only = models.BooleanField(blank=False, null=True)
