import uuid

import reversion
from django.db import models

from cases.models import Case
from users.models import GovUser, ExporterUser


@reversion.register()
class EcjuQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(null=False, blank=False, max_length=5000)
    response = models.CharField(null=True, blank=False, max_length=5000)
    case = models.ForeignKey(Case, related_name='case_ecju_query', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    raised_by_user = models.ForeignKey(GovUser, related_name='govuser_ecju_query', on_delete=models.CASCADE,
                                       default=None, null=False)
    responded_by_user = models.ForeignKey(ExporterUser, related_name='exportuser_ecju_query', on_delete=models.CASCADE,
                                          default=None, null=True)
