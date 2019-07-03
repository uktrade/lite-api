import uuid

import reversion
from django.db import models

from clc_queries.enums import ClcQueryStatus
from end_user.models import EndUser
from goods.models import Good
from organisations.models import Organisation, Site, ExternalLocation
from static.denial_reasons.models import DenialReason


@reversion.register()
class ClcQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    details = models.TextField(default=None, blank=True, null=True)
    good = models.ForeignKey(Good, on_delete=models.DO_NOTHING, null=False)
    status = models.CharField(choices=ClcQueryStatus.choices, default=ClcQueryStatus.SUBMITTED, max_length=50)
