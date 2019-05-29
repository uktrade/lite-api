import uuid
from django.db import models

from applications.models import Application
import reversion

from static.denial_reasons.models import DenialReason


@reversion.register()
class Case(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, related_name='case', on_delete=models.CASCADE)


@reversion.register()
class CaseNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name='case_note', on_delete=models.CASCADE)
    # user = models.ForeignKey(User, related_name='case_note', on_delete=models.CASCADE)
    text = models.TextField(default=None, blank=True, null=True, max_length=2200)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)


@reversion.register()
class CaseDenialReason(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name='case_denial_reason', on_delete=models.CASCADE)
    reasons = models.ManyToManyField(DenialReason)
    reasoning = models.TextField(default=None, blank=True, null=True, max_length=2200)
