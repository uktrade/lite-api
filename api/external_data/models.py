import uuid

from django.db import models
from django.contrib.postgres.fields import JSONField

from api.common.models import TimestampableModel
from api.users.models import GovUser


class Denial(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_by = models.ForeignKey(GovUser, related_name="denials_created", on_delete=models.CASCADE)
    name = models.TextField(help_text="The name of the individual/organization being denied")
    address = models.TextField(help_text="The address of the individual/organization being denied")
    reference = models.TextField(
        help_text="The reference code assigned by the authority that created the denial", unique=True
    )
    data = JSONField()
    is_revoked = models.BooleanField(default=False, help_text="If true do not include in search results")
    is_revoked_comment = models.TextField(default="")
