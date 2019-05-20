import uuid

import reversion
from django.db import models

from addresses.models import Address
from enumchoicefield import ChoiceEnum, EnumChoiceField


class EndUserType(ChoiceEnum):
    government = "Government"
    commercial = "Commercial Organisation"
    other = "Other"


@reversion.register()
class EndUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    address = models.ForeignKey(Address, related_name='enduser', on_delete=models.CASCADE)
    website = models.TextField(default=None, blank=True)
    type = EnumChoiceField(enum_class=EndUserType, default=EndUserType.other)
