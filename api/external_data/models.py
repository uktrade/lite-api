import uuid

from django.db import models

from api.common.models import TimestampableModel
from api.flags.models import Flag
from api.users.models import GovUser


class Denial(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_by = models.ForeignKey(
        GovUser, related_name="denials_created", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    name = models.TextField(
        help_text="The name of the individual/organization being denied", blank=True, default="", null=True
    )
    address = models.TextField(
        help_text="The address of the individual/organization being denied", blank=True, default="", null=True
    )
    reference = models.TextField(help_text="The reference assigned by the notifying government")
    regime_reg_ref = models.TextField(blank=True, default="", null=True)
    notifying_government = models.TextField(
        help_text="The authority that raised the denial", blank=True, default="", null=True
    )
    country = models.TextField(blank=True, default="", null=True)
    item_list_codes = models.TextField("The codes of the items being denied", blank=True, default="", null=True)
    item_description = models.TextField("The description of the item being denied", blank=True, default="", null=True)
    consignee_name = models.TextField(blank=True, default="", null=True)
    end_use = models.TextField(blank=True, default="", null=True)

    data = models.JSONField(default=dict)
    is_revoked = models.BooleanField(default=False, help_text="If true do not include in search results")
    is_revoked_comment = models.TextField(default="")


class SanctionMatch(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    party_on_application = models.ForeignKey(
        "applications.PartyOnApplication", on_delete=models.CASCADE, related_name="sanction_matches"
    )
    elasticsearch_reference = models.TextField()
    name = models.TextField()
    flag_uuid = models.TextField()
    is_revoked = models.BooleanField(default=False, help_text="If true do not include in search results")
    is_revoked_comment = models.TextField(default="")

    def save(self, *args, **kwargs):
        flag = Flag.objects.get(pk=self.flag_uuid)
        if self.is_revoked:
            self.party_on_application.flags.remove(flag)
        else:
            self.party_on_application.flags.add(flag)
        return super().save(*args, **kwargs)
