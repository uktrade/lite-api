import uuid

import reversion
from django.db import models

from addresses.models import Address


@reversion.register()
class Organisation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    eori_number = models.TextField(default=None, blank=True)
    sic_number = models.TextField(default=None, blank=True)
    vat_number = models.TextField(default=None, blank=True)
    registration_number = models.TextField(default=None, blank=True)
    primary_site = models.ForeignKey('Site', related_name='organisation_primary_site', on_delete=models.CASCADE,
                                     blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)


@reversion.register()
class Site(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False)
    address = models.ForeignKey(Address, related_name='site', on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, blank=True, null=True, related_name='site', on_delete=models.CASCADE)


@reversion.register()
class ExternalSite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False)
    address = models.TextField(default=None, blank=False)
    country = models.TextField(default=None, blank=False)
    organisation = models.ForeignKey(Organisation, blank=True, null=True, related_name='external_site', on_delete=models.CASCADE)