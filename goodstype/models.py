import uuid

from django.db import models

from applications.models import BaseApplication
from common.models import TimestampableModel
from flags.models import Flag
from goodstype.constants import DESCRIPTION_MAX_LENGTH
from static.countries.models import Country


class GoodsType(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(default=None, blank=True, null=True, max_length=DESCRIPTION_MAX_LENGTH)
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    control_code = models.TextField(default=None, blank=True, null=True)
    is_good_incorporated = models.BooleanField(default=None, blank=True, null=True)
    limit = models.Q(app_label="applications", model="application")
    application = models.ForeignKey(
        BaseApplication, on_delete=models.CASCADE, related_name="base_application", null=False
    )
    flags = models.ManyToManyField(Flag, related_name="goods_type")
    countries = models.ManyToManyField(Country, related_name="goods_type", default=[])
