from django.db import models

from goods.models import Good
from queries.models import Query
from static.statuses.models import CaseStatus


class ControlListClassificationQuery(Query):
    """
    TODO: Provide comment
    """
    details = models.TextField(default=None, blank=True, null=True)
    good = models.ForeignKey(Good, on_delete=models.DO_NOTHING, null=False, related_name='clc_query')
    status = models.ForeignKey(CaseStatus, related_name='clc_query_status', on_delete=models.CASCADE,
                               blank=True, null=True)
