import uuid

from django.db import models

from applications.models import BaseApplication
from common.models import TimestampableModel


class Licence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        BaseApplication, on_delete=models.CASCADE, null=False, blank=False, related_name="licence"
    )
    start_date = models.DateField(blank=False, null=False)
    duration = models.PositiveSmallIntegerField(blank=False, null=False)
    is_complete = models.BooleanField(default=False, null=False, blank=False)
