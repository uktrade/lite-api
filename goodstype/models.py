import uuid

import reversion
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from applications.models import OpenApplication
from flags.models import Flag


@reversion.register()
class GoodsType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    control_code = models.TextField(default=None, blank=True, null=True)
    is_good_end_product = models.BooleanField(default=None, blank=True, null=True)
    limit = models.Q(app_label='applications', model='application')
    open_application = models.ForeignKey(OpenApplication, on_delete=models.CASCADE, related_name='open_application',
                                         null=False)
    flags = models.ManyToManyField(Flag, related_name='goods_type')
