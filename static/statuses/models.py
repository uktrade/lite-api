from django.db import models


class CaseStatus(models.Model):
    id = models.CharField(max_length=50, blank=False, null=False, unique=True, primary_key=True)
    priority = models.IntegerField(null=False, blank=False)
