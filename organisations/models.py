import uuid
from django.db import models


class Organisation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    eori_number = models.TextField(default=None, blank=True)
    sic_number = models.TextField(default=None, blank=True)
    vat_number = models.TextField(default=None, blank=True)
    address = models.TextField(default=None, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)


class NewOrganisationRequest(models.Model):
    name = models.TextField(default=None, blank=True)
    eori_number = models.TextField(default=None, blank=True)
    sic_number = models.TextField(default=None, blank=True)
    vat_number = models.TextField(default=None, blank=True)
    address = models.TextField(default=None, blank=True)
    admin_user_email = models.EmailField(default=None, blank=True)
