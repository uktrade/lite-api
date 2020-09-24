import uuid

from django.db import models

from api.applications.models import BaseApplication, GoodControlReview
from api.common.models import TimestampableModel
from api.flags.models import Flag
from api.goodstype.constants import DESCRIPTION_MAX_LENGTH
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.models import Country


class GoodsType(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(default=None, blank=True, null=True, max_length=DESCRIPTION_MAX_LENGTH)
    is_good_incorporated = models.BooleanField(default=None, blank=True, null=True)
    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE, related_name="goods_type", null=False)
    flags = models.ManyToManyField(Flag, related_name="goods_type")
    countries = models.ManyToManyField(Country, related_name="goods_type", default=[])
    usage = models.FloatField(null=False, blank=False, default=0)

    # migrate values to GoodControlReview
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    control_list_entries = models.ManyToManyField(ControlListEntry, related_name="goods_types")
    comment = models.TextField(default=None, blank=True, null=True)
    report_summary = models.TextField(default=None, blank=True, null=True)
    
    control_review = models.OneToOneField(GoodControlReview, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "goods_type"
        ordering = ["-created_at"]
