import uuid

import reversion
from django.db import models

from organisations.models import Organisation


@reversion.register()
class Good(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    control_code = models.TextField(default=None, blank=True, null=True)
    is_good_end_product = models.BooleanField(default=None, blank=True, null=True)
    part_number = models.TextField(default=None, blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, default=None)

