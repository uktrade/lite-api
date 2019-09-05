import uuid

from django.db import models
from applications.models import Application
from drafts.models import Draft
from parties.enums import PartyType, ThirdPartyType
from organisations.models import Organisation
from static.countries.models import Country


class Party(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    address = models.TextField(default=None, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    website = models.URLField(default=None, blank=True)
    party_type = models.CharField(choices=PartyType.choices, default=PartyType.OTHER, max_length=20)
    organisation = models.ForeignKey(Organisation, blank=True,
                                     null=True, related_name='organisation_party', on_delete=models.DO_NOTHING)
    application = models.ForeignKey(Application, blank=True,
                                    null=True, related_name='application_party', on_delete=models.DO_NOTHING)
    draft = models.ForeignKey(Draft, blank=True,
                              null=True, related_name='draft_party', on_delete=models.DO_NOTHING)


class ThirdParty(Party):
    third_party_type = models.CharField(choices=ThirdPartyType.choices, default=PartyType.OTHER, max_length=20)
