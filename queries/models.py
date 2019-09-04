import uuid

import reversion
from django.db import models

from end_user.models import EndUser
from goods.models import Good
from static.statuses.models import CaseStatus
from users.models import GovUser, ExporterUser, UserOrganisationRelationship


@reversion.register()
class Query(models.Model):
    """
    Base query class
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)
    status = models.ForeignKey(CaseStatus, related_name='query_status', on_delete=models.CASCADE,
                               blank=True, null=True)

    class Meta:
        ordering = ['-submitted_at']
