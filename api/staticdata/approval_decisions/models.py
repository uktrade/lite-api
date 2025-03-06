import uuid

from django.db import models

from api.cases.models import CaseType
from api.staticdata.decisions.models import Decision


class ApprovalCondition(models.Model):
    id = models.TextField(primary_key=True, editable=False)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    deprecated = models.BooleanField(default=False, null=False, blank=False)
    description = models.TextField(default="")
    display_value = models.TextField(default="")
    case_type = models.ForeignKey(CaseType, on_delete=models.DO_NOTHING, null=False, blank=False)
    decision = models.ForeignKey(Decision, related_name="approval_decision")

    class Meta:
        ordering = ["id"]
