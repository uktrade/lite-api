import reversion
from django.db import models

from cases.models import Case
from organisations.models import Organisation
from static.statuses.models import CaseStatus


@reversion.register()
class Query(Case):
    """
    Base query class
    """

    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)
    status = models.ForeignKey(
        CaseStatus, related_name="query_status", on_delete=models.CASCADE, blank=True, null=True,
    )
