import uuid

from django.db import models

from common.models import TimestampableModel
from documents.models import Document
from flags.models import Flag
from organisations.models import Organisation
from parties.enums import PartyType, SubType, PartyRole
from static.countries.models import Country


class PartyManager(models.Manager):
    def copy_detail(self, pk):
        """
        Copies the details of a party.
        """
        values = dict(
            self.values('name', 'address', 'country', 'website', 'type', 'organisation', 'sub_type', 'copy_of')
            .get(pk=pk)
        )
        if not values["copy_of"]:
            values["copy_of"] = str(pk)
        values["organisation"] = str(values.get("organisation", ""))

        return values


class Party(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    address = models.TextField(default=None, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    website = models.URLField(default=None, blank=True)
    type = models.CharField(choices=PartyType.choices, max_length=20)
    organisation = models.ForeignKey(
        Organisation, blank=True, null=True, related_name="organisation_party", on_delete=models.DO_NOTHING,
    )
    flags = models.ManyToManyField(Flag, related_name="parties")
    sub_type = models.CharField(choices=SubType.choices, default=SubType.OTHER, max_length=20)
    role = models.CharField(choices=PartyRole.choices, default=PartyRole.OTHER, max_length=22, null=True)
    # FK is self referencing
    copy_of = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)

    objects = PartyManager()


class PartyDocument(Document):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
