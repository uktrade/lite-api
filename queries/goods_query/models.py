from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from goods.models import Good
from queries.models import Query
from users.models import ExporterNotification


class GoodsQuery(Query):
    """
    Query into getting the correct control list classification for a good
    """

    clc_raised_reasons = models.TextField(default=None, blank=True, null=True, max_length=2000)
    pv_grading_raised_reasons = models.TextField(default=None, blank=True, null=True, max_length=2000)
    good = models.ForeignKey(Good, on_delete=models.DO_NOTHING, null=False, related_name="good")

    clc_responded = models.BooleanField(default="False")
    pv_grading_responded = models.BooleanField(default="False")

    notifications = GenericRelation(ExporterNotification, related_query_name="goodsquery")
