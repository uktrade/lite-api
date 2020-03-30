import uuid

from django.db import models

from static.countries.models import Country


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address_line_1 = models.CharField(default=None, blank=True, null=True, max_length=50)
    address_line_2 = models.CharField(default=None, blank=True, null=True, max_length=50)
    region = models.CharField(default=None, blank=True, null=True, max_length=50)
    postcode = models.CharField(default=None, blank=True, null=True, max_length=10)
    city = models.CharField(default=None, blank=False, null=True, max_length=50)

    address = models.CharField(
        default=None, blank=True, null=True, max_length=256, help_text="Used for addresses not in the UK"
    )
    country = models.ForeignKey(Country, blank=False, null=False, on_delete=models.CASCADE)

    class Meta:
        db_table = "address"
