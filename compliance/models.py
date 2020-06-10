import uuid

from django.db import models
from django.db.models import deletion

from licences.models import Licence
from organisations.models import Organisation


class OpenLicenceReturns(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(Organisation, on_delete=deletion.CASCADE)
    file = models.TextField(blank=False, null=False)
    year = models.PositiveSmallIntegerField(blank=False, null=False)
    licences = models.ManyToManyField(Licence, related_name="open_licence_returns")
