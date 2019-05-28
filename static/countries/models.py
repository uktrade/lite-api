from django.db import models


class Country(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    report_name = models.CharField(max_length=100)
