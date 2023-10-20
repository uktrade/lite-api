from django.db import models

from api.flags.models import Flag


class CountryManager(models.Manager):
    def get_by_natural_key(self, pk):
        return self.get(pk=pk)


class ExcludeSpecialCountryManager(CountryManager):
    def get_queryset(self):
        return super().get_queryset().exclude(id="UKCS")


class Country(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=10)  # Country Code
    trading_country_code = models.CharField(null=True, max_length=2)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    flags = models.ManyToManyField(Flag, related_name="countries")
    is_eu = models.BooleanField()
    report_name = models.TextField(help_text="Name to use in reports, to harmonize with SPIRE", default="")

    objects = CountryManager()
    exclude_special_countries = ExcludeSpecialCountryManager()

    def natural_key(self):
        return (self.pk,)
