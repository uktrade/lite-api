from django.db import models
from static.statuses.enums import CaseStatusEnum


class CaseStatus(models.Model):
    id = models.CharField(max_length=50, blank=False, null=False, unique=True, primary_key=True)
    name = models.CharField(choices=CaseStatusEnum.choices, default=CaseStatusEnum.SUBMITTED, max_length=50)
    priority = models.IntegerField(null=False, blank=False)
