import uuid

import reversion
from django.db import models

from addresses.models import Address

@reversion.register()
class EndUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    dress = models.ForeignKey(Address, related_name='site', on_delete=models.CASCADE)
    website = models.TextField(default=None, blank=True)