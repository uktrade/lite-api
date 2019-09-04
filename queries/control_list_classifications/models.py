from django.db import models

from goods.models import Good
from queries.models import Query


class ControlListClassificationQuery(Query):
    """
    TODO: Provide comment
    """
    details = models.TextField(default=None, blank=True, null=True)
    good = models.ForeignKey(Good, on_delete=models.DO_NOTHING, null=False, related_name='clc_query')
