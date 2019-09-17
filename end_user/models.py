import uuid

from django.db import models

from end_user.enums import EndUserType
from organisations.models import Organisation
from static.countries.models import Country


class EndUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    address = models.TextField(default=None, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    website = models.URLField(default=None, blank=True)
    type = models.CharField(choices=EndUserType.choices, default=EndUserType.OTHER, max_length=20)
    organisation = models.ForeignKey(Organisation, blank=True,
                                     null=True, related_name='organisation_end_user', on_delete=models.CASCADE)
