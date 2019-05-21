import uuid

from django.db import models

from enumchoicefield import ChoiceEnum, EnumChoiceField

from organisations.models import Organisation


class EndUserType(ChoiceEnum):
    government = "Government"
    commercial = "Commercial Organisation"
    other = "Other"


class EndUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    address = models.TextField(default=None, blank=True)
    country = models.TextField(default=None, blank=True)
    website = models.TextField(default=None, blank=True)
    type = EnumChoiceField(enum_class=EndUserType, default=EndUserType.other)
    organisation = models.ForeignKey(Organisation, blank=True,
                                     null=True, related_name='enduser', on_delete=models.CASCADE)

