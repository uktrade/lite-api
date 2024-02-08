import uuid
from django.db import models

from api.common.models import TimestampableModel


# Create your models here.
class Survey(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    recommendation = models.CharField(max_length=255)
    other_detail = models.CharField(max_length=255, blank=True, null=True)
    experienced_issue = models.JSONField(blank=True, null=True)
    helpful_guidance = models.CharField(max_length=255, blank=True, null=True)
    user_account_process = models.CharField(max_length=255, blank=True, null=True)
    service_improvements_feedback = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return "Survey #{0} - {1}".format(self.id, self.recommendation)
