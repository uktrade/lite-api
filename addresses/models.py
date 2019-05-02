from django.db import models
import uuid
import reversion


@reversion.register()
class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.TextField(default=None, blank=False)
    address_line_1 = models.TextField(default=None, blank=False)
    address_line_2 = models.TextField(default=None, blank=True, null=True)
    state = models.TextField(default=None, blank=False)
    zip_code = models.CharField(max_length=10)
    city = models.TextField(default=None, blank=False)
