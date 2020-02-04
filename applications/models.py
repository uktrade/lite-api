import uuid

from django.db import models
from django.utils import timezone

from applications.enums import ApplicationType, ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.managers import BaseApplicationManager, HmrcQueryManager
from cases.models import Case
from common.models import TimestampableModel
from documents.models import Document
from goods.models import Good
from lite_content.lite_api.strings import Parties
from organisations.models import Organisation, Site, ExternalLocation
from parties.enums import PartyType
from parties.models import Party
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.case_status_validate import is_case_status_draft
from static.units.enums import Units


class ApplicationException(Exception):
    def __init__(self, data=None, *args, **kwargs):
        self.data = data


class ApplicationPartyMixin:
    def add_party(self, party):
        old_poa = None

        if PartyOnApplication.objects.filter(party=party).exclude(application=self).exists():
            # Party cannot be used in multiple applications
            raise ApplicationException({"error": "Party exists"})

        if party.type == PartyType.ULTIMATE_END_USER:
            # Rule: Append
            pass

        elif party.type in [PartyType.END_USER, PartyType.CONSIGNEE] and getattr(self, party.type, False):
            # Rule: Replace
            old_poa = getattr(self, party.type)
            old_poa.deleted_at = timezone.now()
            old_poa.save()

        elif party.type == PartyType.THIRD_PARTY:
            # Rule: Append
            if not party.role:
                raise ApplicationException({"errors": {"required": Parties.ThirdParty.NULL_ROLE}})

        poa = PartyOnApplication.objects.create(application=self, party=party)

        return poa.party, old_poa.party if old_poa else None

    def delete_party(self, poa):
        poa.deleted_at = timezone.now()
        poa.save()

    def is_major_editable(self):
        return not (
                not is_case_status_draft(self.status.status)
                and self.status.status != CaseStatusEnum.APPLICANT_EDITING
        )

    def is_editable(self):
        return not CaseStatusEnum.is_read_only(self.status.status)

    def party_is_editable(self, party):
        # Check if party is in editable state
        if party.type in [PartyType.ULTIMATE_END_USER, PartyType.THIRD_PARTY]:
            is_editable = self.is_editable()
        elif party.type in [PartyType.CONSIGNEE, PartyType.END_USER]:
            is_editable = self.is_major_editable()
        else:
            is_editable = False

        return is_editable

    @property
    def parties_on_application(self):
        return (
            self.parties.filter(deleted_at__isnull=True)
            .prefetch_related('party__flags').select_related('party', 'party__organisation', 'party__country')
        )

    @property
    def consignee(self):
        """
        Backwards compatible
        Standard and HMRC Query applications
        """
        try:
            return self.parties_on_application.get(party__type=PartyType.CONSIGNEE)
        except PartyOnApplication.DoesNotExist:
            pass

    @property
    def end_user(self):
        """
        Backwards compatible
        Standard and HMRC Query applications
        """
        try:
            return self.parties_on_application.get(party__type=PartyType.END_USER)
        except PartyOnApplication.DoesNotExist:
            pass

    @property
    def ultimate_end_users(self):
        """
        Backwards compatible
        Standard and HMRC Query applications
        """
        return self.parties_on_application.filter(party__type=PartyType.ULTIMATE_END_USER)

    @property
    def third_parties(self):
        """
        Backwards compatible
        Standard and HMRC Query applications
        """
        qs = self.parties.filter(deleted_at__isnull=True).select_related('party', 'party__organisation').prefetch_related('party__flags')
        return qs.filter(party__type=PartyType.THIRD_PARTY)


class BaseApplication(ApplicationPartyMixin, Case):
    name = models.TextField(default=None, blank=True, null=True)
    application_type = models.CharField(choices=ApplicationType.choices, default=None, max_length=50)
    activity = models.TextField(default=None, blank=True, null=True)
    usage = models.TextField(default=None, blank=True, null=True)
    licence_duration = models.IntegerField(default=None, null=True, help_text="Set when application finalised")

    objects = BaseApplicationManager()


class StandardApplication(BaseApplication):
    export_type = models.CharField(choices=ApplicationExportType.choices, default=None, max_length=50)
    reference_number_on_information_form = models.TextField(blank=True, null=True)
    have_you_been_informed = models.CharField(
        choices=ApplicationExportLicenceOfficialType.choices, default=None, max_length=50,
    )


class OpenApplication(BaseApplication):
    export_type = models.CharField(choices=ApplicationExportType.choices, default=None, max_length=50)


class ExhibitionClearanceApplication(BaseApplication):
    pass

class HmrcQuery(BaseApplication):
    hmrc_organisation = models.ForeignKey(Organisation, default=None, on_delete=models.PROTECT)
    reasoning = models.CharField(default=None, blank=True, null=True, max_length=1000)
    have_goods_departed = models.BooleanField(default=False)  # Signal in signals.py

    objects = HmrcQueryManager()


class ApplicationDocument(Document):
    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)


class SiteOnApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, related_name="sites_on_application", on_delete=models.CASCADE)
    application = models.ForeignKey(BaseApplication, related_name="application_sites", on_delete=models.CASCADE)


class ApplicationDenialReason(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        BaseApplication, related_name="application_denial_reason", on_delete=models.CASCADE,
    )
    reasons = models.ManyToManyField(DenialReason)
    reason_details = models.TextField(default=None, blank=True, null=True, max_length=2200)


class ExternalLocationOnApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_location = models.ForeignKey(
        ExternalLocation, related_name="external_locations_on_application", on_delete=models.CASCADE,
    )
    application = models.ForeignKey(
        BaseApplication, related_name="external_application_sites", on_delete=models.CASCADE,
    )


class GoodOnApplication(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good = models.ForeignKey(Good, related_name="goods_on_application", on_delete=models.CASCADE)
    application = models.ForeignKey(BaseApplication, related_name="goods", on_delete=models.CASCADE)
    quantity = models.FloatField(null=True, blank=True, default=None)
    unit = models.CharField(choices=Units.choices, default=Units.GRM, max_length=50)
    value = models.DecimalField(max_digits=256, decimal_places=2)
    is_good_incorporated = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]


class CountryOnApplication(models.Model):
    """
    Open licence applications export to countries, instead of an end user
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(OpenApplication, related_name="application_countries", on_delete=models.CASCADE)
    country = models.ForeignKey(Country, related_name="countries_on_application", on_delete=models.CASCADE)


class PartyOnApplication(TimestampableModel):
    application = models.ForeignKey(
        BaseApplication,
        on_delete=models.CASCADE,
        related_name="parties",
        related_query_name='party',
    )
    party = models.ForeignKey(Party, on_delete=models.PROTECT)
    deleted_at = models.DateTimeField(null=True, default=None)

    objects = models.Manager()

    def __repr__(self):
        return str({'application': self.application.id, 'party_type': self.party.type, 'deleted_at': self.deleted_at, 'party_id': self.party.id})
