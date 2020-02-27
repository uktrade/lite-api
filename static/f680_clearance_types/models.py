from django.db import models

from static.f680_clearance_types.enums import F680ClearanceTypeEnum


class F680ClearanceType(models.Model):
    id = models.CharField(
        null=False, blank=False, primary_key=True, max_length=45
    )
