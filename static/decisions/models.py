import uuid

from django.db import models

from cases.enums import AdviceType


class Decision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(choices=AdviceType.choices, null=False, blank=False, max_length=45)
