from django.db import models


class Country(models.Model):
    id = models.CharField(primary_key=True, max_length=100)  # Country Code
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
