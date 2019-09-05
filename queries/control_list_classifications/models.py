from django.db import models

from goods.models import Good
from queries.models import Query


class ControlListClassificationQuery(Query):
    """
    Query into getting the correct control list classification
    for a good
    """
    details = models.TextField(default=None, blank=True, null=True)
    good = models.ForeignKey(Good, on_delete=models.DO_NOTHING, null=False, related_name='clc_query')
