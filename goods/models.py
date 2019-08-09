import uuid

import reversion
from django.db import models

from goods.enums import GoodStatus, GoodControlled
from organisations.models import Organisation


@reversion.register()
class Good(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
    is_good_controlled = models.CharField(choices=GoodControlled.choices, default=GoodControlled.UNSURE, max_length=20)
    control_code = models.TextField(default=None, blank=True, null=True)
    is_good_end_product = models.BooleanField(default=None, blank=True, null=True)
    part_number = models.TextField(default=None, blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, default=None)
    status = models.CharField(choices=GoodStatus.choices, default=GoodStatus.DRAFT, max_length=20)
