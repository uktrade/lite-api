import uuid

import reversion
from django.db import models
from goods.models import Good
from static.statuses.models import CaseStatus


@reversion.register()
class ClcQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    details = models.TextField(default=None, blank=True, null=True)
    good = models.ForeignKey(Good, on_delete=models.DO_NOTHING, null=False, related_name='clc_query')
    status = models.ForeignKey(CaseStatus, related_name='clc_query_status', on_delete=models.CASCADE,
                               default=None, blank=True, null=True)
