from django.db import models


class FakeModel(models.Model):
    thing = models.CharField(max_length=100)
