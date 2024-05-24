import uuid

from django.db import models

from api.common.models import TimestampableModel
from api.flags.models import Flag
from api.users.models import GovUser
from api.external_data.enums import DenialEntityType


class Denial(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_by_user = models.ForeignKey(
        GovUser, related_name="denial_created_by_user", on_delete=models.DO_NOTHING, null=True, blank=True
    )
    reference = models.TextField(help_text="The reference assigned by the notifying government")
    regime_reg_ref = models.TextField(unique=True, help_text="The unique reference assigned by the issuing regime")
    notifying_government = models.TextField(
        help_text="The authority that raised the denial", null=True, blank=True, default=""
    )
    denial_cle = models.TextField("The codes of the items being denied", null=True, blank=True, default="")
    item_description = models.TextField("The description of the item being denied", null=True, blank=True, default="")
    end_use = models.TextField(null=True, blank=True, default="")
    is_revoked = models.BooleanField(default=False, help_text="If true do not include in search results")
    is_revoked_comment = models.TextField(null=True, blank=True, default="")
    reason_for_refusal = models.TextField(
        help_text="Reason why the denial was refused", null=True, blank=True, default=""
    )


class DenialEntity(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    denial = models.ForeignKey(Denial, related_name="denial_entity", on_delete=models.CASCADE, blank=True, null=True)

    created_by = models.ForeignKey(
        GovUser, related_name="denialenitity_created", on_delete=models.DO_NOTHING, blank=True, null=True
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
    denial_cle = models.TextField("The codes of the items being denied", blank=True, default="", null=True)
    item_description = models.TextField("The description of the item being denied", blank=True, default="", null=True)
    consignee_name = models.TextField(blank=True, default="", null=True)
    end_use = models.TextField(blank=True, default="", null=True)

    data = models.JSONField(default=dict)
    is_revoked = models.BooleanField(default=False, help_text="If true do not include in search results")
    is_revoked_comment = models.TextField(default="")
    reason_for_refusal = models.TextField(
        help_text="Reason why the denial was refused", blank=True, default="", null=True
    )
    spire_entity_id = models.IntegerField(help_text="Entity_id from spire for matching data", null=True)
    entity_type = models.TextField(
        choices=DenialEntityType.choices, help_text="Type of entity being denied", blank=True, default="", null=True
    )


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
