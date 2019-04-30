import uuid
from django.db import models
import reversion
from sites.models import Site
from django.db.models.deletion import PROTECT


@reversion.register()
class Organisation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    eori_number = models.TextField(default=None, blank=True)
    sic_number = models.TextField(default=None, blank=True)
    vat_number = models.TextField(default=None, blank=True)
    registration_number = models.TextField(default=None, blank=True)
    primary_site = models.ForeignKey(Site, related_name='organisation', on_delete=PROTECT)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
