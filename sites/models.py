import uuid
import reversion
from django.db import models

from addresses.models import Address
from organisations.models import Organisation


@reversion.register()
class Site(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False)
    address = models.ForeignKey(Address, related_name='site', on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, related_name='site', on_delete=models.CASCADE)
