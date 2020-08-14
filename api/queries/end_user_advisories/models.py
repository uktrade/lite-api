from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from api.users.models import ExporterNotification
from api.parties.models import Party
from api.queries.models import Query


class EndUserAdvisoryQuery(Query):
    """
    Query into ensuring that an end user is valid
    """

    end_user = models.ForeignKey(Party, on_delete=models.DO_NOTHING, null=False, related_name="eua_query")
    note = models.TextField(default=None, blank=True, null=True)
    reasoning = models.TextField(default=None, blank=True, null=True)
    nature_of_business = models.TextField(default=None, blank=True, null=True)
    contact_name = models.TextField(default=None, blank=True, null=True)
    contact_email = models.EmailField(default=None, blank=True)
    contact_job_title = models.TextField(default=None, blank=True, null=True)
    contact_telephone = models.CharField(max_length=15, default=None, null=False)

    notifications = GenericRelation(ExporterNotification, related_query_name="eua_query")

    class Meta:
        ordering = ["created_at"]
