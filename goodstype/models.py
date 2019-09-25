import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from flags.models import Flag
from static.countries.models import Country


class GoodsType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    control_code = models.TextField(default=None, blank=True, null=True)
    is_good_end_product = models.BooleanField(default=None, blank=True, null=True)
    limit = models.Q(app_label='applications', model='application') | \
            models.Q(app_label='drafts', model='draft')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=limit)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    flags = models.ManyToManyField(Flag, related_name='goods_type')
    countries = models.ManyToManyField(Country, related_name='goods_type', default=[])
