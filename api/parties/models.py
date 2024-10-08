import uuid

from django.db import models

from api.common.models import TimestampableModel
from api.core.model_mixins import Clonable
from api.documents.models import Document
from api.flags.models import Flag
from api.goods.enums import PvGrading
from api.organisations.models import Organisation
from api.parties.enums import PartyType, SubType, PartyRole, PartyDocumentType
from api.staticdata.countries.models import Country
import reversion


class PartyManager(models.Manager):
    def all(self):
        return self.get_queryset().exclude(type=PartyType.ADDITIONAL_CONTACT)

    def additional_contacts(self):
        return self.get_queryset().filter(type=PartyType.ADDITIONAL_CONTACT)

    def copy_detail(self, pk):
        """
        Copies the details of a party.
        """
        qs = self.values(
            "name",
            "address",
            "country",
            "website",
            "signatory_name_euu",
            "type",
            "organisation",
            "sub_type",
            "sub_type_other",
            "copy_of",
        )
        values = dict(qs.get(pk=pk))
        if not values["copy_of"]:
            values["copy_of"] = str(pk)
        values["organisation"] = str(values.get("organisation", ""))
        if "signatory_name_euu" in values:
            values["signatory_name_euu"] = ""

        return values


@reversion.register()
class Party(TimestampableModel, Clonable):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default="", blank=True)
    address = models.TextField(default=None, blank=True, max_length=256)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    website = models.URLField(default=None, blank=True, null=True)
    signatory_name_euu = models.TextField(blank=True)
    type = models.CharField(choices=PartyType.choices, max_length=20)
    organisation = models.ForeignKey(
        Organisation, blank=True, null=True, related_name="organisation_party", on_delete=models.DO_NOTHING
    )
    flags = models.ManyToManyField(Flag, related_name="parties")
    role = models.CharField(
        choices=PartyRole.choices, default=PartyRole.OTHER, max_length=22, null=True, help_text="Third party type only"
    )
    role_other = models.CharField(max_length=75, default=None, null=True)
    sub_type = models.CharField(choices=SubType.choices, default=SubType.OTHER, max_length=20)
    sub_type_other = models.CharField(max_length=75, default=None, null=True)
    end_user_document_available = models.BooleanField(blank=True, null=True)
    end_user_document_missing_reason = models.TextField(blank=True, default="")
    product_differences_note = models.TextField(blank=True, default="")
    document_in_english = models.BooleanField(blank=True, null=True)
    document_on_letterhead = models.BooleanField(blank=True, null=True)
    ec3_missing_reason = models.TextField(blank=True, default="")
    clearance_level = models.CharField(
        choices=PvGrading.choices, max_length=30, null=True, help_text="Only relevant to F680 applications"
    )
    descriptors = models.CharField(max_length=256, null=True, help_text="Clearance descriptors, caveats and codewords")
    # FK is self referencing
    copy_of = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)
    phone_number = models.CharField(null=True, blank=True, max_length=50)
    email = models.EmailField(null=True, blank=True)
    details = models.TextField(null=True, blank=True, max_length=256)

    objects = PartyManager()

    class Meta:
        ordering = ["name"]

    clone_exclusions = [
        "id",
        "flags",
        "copy_of",
    ]
    clone_mappings = {
        "organisation": "organisation_id",
        "country": "country_id",
    }

    def clone(self, exclusions=None, **overrides):
        cloned_party = super().clone(exclusions=exclusions, **overrides)
        cloned_party.copy_of = self
        cloned_party.save()

        party_documents = PartyDocument.objects.filter(party=self, safe=True)
        for party_document in party_documents:
            party_document.clone(party=cloned_party)

        return cloned_party


class PartyDocument(Document, Clonable):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    type = models.TextField(choices=PartyDocumentType.choices, default=PartyDocumentType.SUPPORTING_DOCUMENT)
    description = models.TextField(blank=True, default="")

    clone_exclusions = [
        "id",
        "party",
        "document_ptr",
    ]
