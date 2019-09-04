from django.db import models

from end_user.models import EndUser
from queries.models import Query
from static.statuses.models import CaseStatus


class EndUserAdvisoryQuery(Query):
    """
    TODO: Provide comment
    """
    end_user = models.ForeignKey(EndUser, on_delete=models.DO_NOTHING, null=False, related_name='euae_query')
    details = models.TextField(default=None, blank=True, null=True)
    status = models.ForeignKey(CaseStatus, related_name='euae_query_status', on_delete=models.CASCADE,
                               blank=True, null=True)
    raised_reason = models.TextField(default=None, blank=True, null=True)
