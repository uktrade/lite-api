from api.common.models import TimestampableModel
from api.users.models import GovUser

from django.db import models
from django.contrib.postgres.fields import JSONField


class Denial(TimestampableModel):
    created_by = models.ForeignKey(GovUser, related_name="denials_created", on_delete=models.CASCADE)
    denied_name = models.TextField(help_text="The name of the person being denied")
    authority = models.TextField(help_text="The organisation that denied the person")
    data = JSONField()
