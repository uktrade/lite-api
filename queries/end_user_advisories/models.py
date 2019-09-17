from django.db import models

from end_user.models import EndUser
from queries.models import Query


class EndUserAdvisoryQuery(Query):
    """
    Query into ensuring that an end user is valid
    """
    end_user = models.ForeignKey(EndUser, on_delete=models.DO_NOTHING, null=False, related_name='euae_query')
    note = models.TextField(default=None, blank=True, null=True)
    reasoning = models.TextField(default=None, blank=True, null=True)
    copy_of = models.ForeignKey('self', default=None, null=True, on_delete=models.CASCADE)
