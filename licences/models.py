import uuid

from django.db import models

from applications.models import BaseApplication
from cases.models import FinalAdvice
from common.models import TimestampableModel
from static.decisions.models import Decision


class Licence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        BaseApplication, on_delete=models.CASCADE, null=False, blank=False, related_name="licence"
    )
    start_date = models.DateField(blank=False, null=False)
    duration = models.PositiveSmallIntegerField(blank=False, null=False)
    is_complete = models.BooleanField(default=False, null=False, blank=False)
    decisions = models.ManyToManyField(Decision, related_name="licence")
