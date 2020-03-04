import uuid

from django.db import models

from static.decisions.enums import Decisions


class Decision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(choices=Decisions.choices, null=False, blank=False, max_length=45)
