import uuid

from django.db import models

from api.static.f680_clearance_types.enums import F680ClearanceTypeEnum


class F680ClearanceType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(choices=F680ClearanceTypeEnum.choices, null=False, blank=False, max_length=45)
