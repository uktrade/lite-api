from django.db import models

from cases.models import Case
from common.models import CreatedAt
from licences.models import Licence
from organisations.models import Organisation


class ComplianceSiteCase(Case):
    site = models.OneToOneField("organisations.Site", related_name="compliance", on_delete=models.DO_NOTHING,)
