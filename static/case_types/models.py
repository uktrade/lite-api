from django.db import models

from static.case_types.enums import CaseTypeEnum


class CaseType(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=30)
    name = models.CharField(choices=CaseTypeEnum.choices, null=False, max_length=35)
