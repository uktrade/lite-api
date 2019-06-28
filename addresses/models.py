import uuid

import reversion
from django.db import models


@reversion.register()
class Address(models.Model):
    """
    Used for address fields
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.TextField(default=None, blank=False)
    address_line_1 = models.TextField(default=None, blank=False)
    address_line_2 = models.TextField(default=None, blank=True, null=True)
    region = models.TextField(default=None, blank=False)
    postcode = models.CharField(max_length=10)
    city = models.TextField(default=None, blank=False)
