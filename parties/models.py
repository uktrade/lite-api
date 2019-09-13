import uuid

from django.db import models
from parties.enums import PartyType, SubType, ThirdPartySubType
from organisations.models import Organisation
from static.countries.models import Country


class Party(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    address = models.TextField(default=None, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    website = models.URLField(default=None, blank=True)
    type = models.CharField(choices=PartyType.choices, max_length=20)
    organisation = models.ForeignKey(Organisation, blank=True,
                                     null=True, related_name='organisation_party', on_delete=models.DO_NOTHING)


class Consignee(Party):
    sub_type = models.CharField(choices=SubType.choices,
                                default=SubType.OTHER, max_length=20)

    def save(self, *args, **kwargs):
        self.type = PartyType.CONSIGNEE
        super(Consignee, self).save(*args, **kwargs)


class EndUser(Party):
    sub_type = models.CharField(choices=SubType.choices,
                                default=SubType.OTHER, max_length=20)

    def save(self, *args, **kwargs):
        self.type = PartyType.END
        super(EndUser, self).save(*args, **kwargs)


class UltimateEndUser(Party):
    sub_type = models.CharField(choices=SubType.choices,
                                default=SubType.OTHER, max_length=20)

    def save(self, *args, **kwargs):
        self.type = PartyType.ULTIMATE
        super(UltimateEndUser, self).save(*args, **kwargs)


class ThirdParty(Party):
    sub_type = models.CharField(choices=ThirdPartySubType.choices,
                                default=ThirdPartySubType.OTHER, max_length=20)

    def save(self, *args, **kwargs):
        self.type = PartyType.THIRD
        super(ThirdParty, self).save(*args, **kwargs)
