from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from api.goods.models import Good
from api.queries.models import Query
from api.users.models import ExporterNotification


class GoodsQuery(Query):
    """
    Query into getting the correct control list classification for a good
    """

    clc_control_list_entry = models.TextField(default=None, blank=True, null=True, max_length=200)
    clc_raised_reasons = models.TextField(default=None, blank=True, null=True, max_length=2000)
    pv_grading_raised_reasons = models.TextField(default=None, blank=True, null=True, max_length=2000)
    good = models.ForeignKey(Good, on_delete=models.DO_NOTHING, null=False, related_name="good")

    clc_responded = models.BooleanField(default=None, null=True)
    pv_grading_responded = models.BooleanField(default=None, null=True)

    notifications = GenericRelation(ExporterNotification, related_query_name="goods_query")
