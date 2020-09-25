import uuid

from django.db import models

from api.applications.models import AbstractGoodOnApplication, BaseApplication
from api.common.models import TimestampableModel
from api.flags.models import Flag
from api.goodstype.constants import DESCRIPTION_MAX_LENGTH
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.models import Country


class GoodsType(AbstractGoodOnApplication):
    description = models.TextField(default=None, blank=True, null=True, max_length=DESCRIPTION_MAX_LENGTH)
    countries = models.ManyToManyField(Country, related_name="goods_type", default=[])
    usage = models.FloatField(null=False, blank=False, default=0)
    flags = models.ManyToManyField(Flag, related_name="goods_type")

    class Meta:
        db_table = "goods_type"
        ordering = ["-created_at"]
        default_related_name = "goods_type"
