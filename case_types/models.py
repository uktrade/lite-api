import uuid

import reversion
from django.db import models
from end_user.models import EndUser
from goods.models import Good
from organisations.models import Organisation, Site, ExternalLocation
from static.denial_reasons.models import DenialReason


@reversion.register()
class CaseType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False, null=False)
