from django.db import models

from api.flags.models import Flag


class CountryManager(models.Manager):
    def get_queryset(self):
        return super(CountryManager, self).get_queryset().exclude(id="UKCS")


class Country(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=10)  # Country Code
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    flags = models.ManyToManyField(Flag, related_name="countries")
    is_eu = models.BooleanField()
    report_name = models.TextField(help_text="Name to use in reports, to harmonize with SPIRE", default="")

    objects = models.Manager()
    exclude_special_countries = CountryManager()
