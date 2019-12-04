from django.db import models

from static.case_types.enums import CaseType


class CaseType(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=30)
    name = models.CharField(choices=CaseType.choices, null=False, max_length=35)
