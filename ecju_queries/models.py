import uuid

import reversion
from django.db import models

from cases.models import Case


@reversion.register()
class EcjuQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(null=False, blank=False, max_length=5000)
    response = models.CharField(null=True, blank=False, max_length=5000)
    case = models.ForeignKey(Case, related_name='case_ecju_query', on_delete=models.CASCADE)
