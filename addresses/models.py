import uuid

from django.db import models

from static.countries.models import Country


class Address(models.Model):
    """
    Used for address fields
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address_line_1 = models.TextField(default=None, blank=False)
    address_line_2 = models.TextField(default=None, blank=True, null=True)
    region = models.TextField(default=None, blank=False)
    postcode = models.CharField(max_length=10)
    city = models.TextField(default=None, blank=False)
    country = models.ForeignKey(Country, blank=False, null=False, on_delete=models.CASCADE)
