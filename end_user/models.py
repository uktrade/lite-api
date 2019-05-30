import uuid

from django.db import models

from organisations.models import Organisation


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
    country = models.TextField(default=None, blank=True)
    website = models.URLField(default=None, blank=True)
    type = models.CharField(choices=END_USER_TYPE, default='other', max_length=20)
    organisation = models.ForeignKey(Organisation, blank=True,
                                     null=True, related_name='organisation_end_user', on_delete=models.CASCADE)
