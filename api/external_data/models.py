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
    reference = models.TextField(help_text="The reference assigned by the notifying government", unique=True)
    notifying_government = models.TextField(help_text="The authority that raised the denial")
    final_destination = models.TextField()
    item_list_codes = models.TextField("The codes of the items being denied")
    item_description = models.TextField("The description of the item being denied")
    consignee_name = models.TextField()
    end_use = models.TextField()

    data = JSONField()
    is_revoked = models.BooleanField(default=False, help_text="If true do not include in search results")
    is_revoked_comment = models.TextField(default="")


class SanctionMatch(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    party_on_application = models.ForeignKey(
        "applications.PartyOnApplication", on_delete=models.CASCADE, related_name="sanction_matches"
    )
    elasticsearch_reference = models.TextField()
