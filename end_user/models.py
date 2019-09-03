import uuid

from django.db import models

from end_user.enums import EndUserType
from organisations.models import Organisation
from static.countries.models import Country
from static.statuses.models import CaseStatus


class EndUser(models.Model):
    GOVERNMENT = 'government'
    COMMERCIAL = 'commercial'
    INDIVIDUAL = 'individual'
    OTHER = 'other'
    END_USER_TYPE = [
        (GOVERNMENT, 'Government'),
        (COMMERCIAL, 'Commercial Organisation'),
        (INDIVIDUAL, 'Individual'),
        (OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    address = models.TextField(default=None, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    website = models.URLField(default=None, blank=True)
    type = models.CharField(choices=EndUserType.choices, default=EndUserType.OTHER, max_length=20)
    organisation = models.ForeignKey(Organisation, blank=True,
                                     null=True, related_name='organisation_end_user', on_delete=models.CASCADE)


class EUAEQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    end_user = models.ForeignKey(EndUser, on_delete=models.DO_NOTHING, null=False, related_name='euae_query')  # many=True?
    details = models.TextField(default=None, blank=True, null=True)
    status = models.ForeignKey(CaseStatus, related_name='euae_query_status', on_delete=models.CASCADE,
                               blank=True, null=True)
    raised_reason = models.TextField(null=False)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)
