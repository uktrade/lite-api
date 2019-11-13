import uuid
from django.db import models

from applications.models import OpenApplication
from flags.models import Flag
from static.countries.models import Country


class GoodsType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    control_code = models.TextField(default=None, blank=True, null=True)
    is_good_end_product = models.BooleanField(default=None, blank=True, null=True)
    limit = models.Q(app_label="applications", model="application")
    application = models.ForeignKey(
        OpenApplication,
        on_delete=models.CASCADE,
        related_name="open_application",
        null=False,
    )
    flags = models.ManyToManyField(Flag, related_name="goods_type")
    countries = models.ManyToManyField(Country, related_name="goods_type", default=[])
