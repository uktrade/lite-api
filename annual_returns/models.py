import uuid

from django.db import models

from licences.models import Licence


class OpenLicenceReturns(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField(blank=False, null=False)
    year = models.PositiveSmallIntegerField(blank=False, null=False)
    licences = models.ManyToManyField(Licence, related_name="open_licence_returns")
