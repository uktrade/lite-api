from cases.models import Case
import uuid

from django.db import models
from django.db.models import deletion

from common.models import CreatedAt
from licences.models import Licence
from organisations.models import Organisation


class ComplianceSiteCase(Case):
    site = models.OneToOneField("organisations.Site", related_name="compliance", on_delete=models.DO_NOTHING,)


class OpenLicenceReturns(CreatedAt):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(Organisation, on_delete=deletion.CASCADE)
    returns_data = models.TextField()
    year = models.PositiveSmallIntegerField()
    licences = models.ManyToManyField(Licence, related_name="open_licence_returns")
