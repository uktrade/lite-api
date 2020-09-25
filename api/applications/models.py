import uuid

from django.db import models
from django.utils import timezone
from rest_framework.exceptions import APIException
from separatedvaluesfield.models import SeparatedValuesField

from api.applications.enums import (
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
    ServiceEquipmentType,
    MTCRAnswers,
    GoodsTypeCategory,
    ContractType,
)

from api.applications.managers import BaseApplicationManager, HmrcQueryManager
from api.cases.enums import CaseTypeEnum
from api.cases.models import Case
from api.common.models import TimestampableModel
from api.documents.models import Document
from api.flags.models import Flag
from api.goods.enums import GoodStatus, ItemType, PvGrading
from api.goods.models import Good
from api.organisations.models import Organisation, Site, ExternalLocation
from api.parties.enums import PartyType
from api.parties.models import Party
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.models import Country
from api.staticdata.denial_reasons.models import DenialReason
from api.staticdata.f680_clearance_types.models import F680ClearanceType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.case_status_validate import is_case_status_draft
from api.staticdata.trade_control.enums import TradeControlProductCategory, TradeControlActivity
from api.staticdata.units.enums import Units
from lite_content.lite_api.strings import PartyErrors


class ApplicationException(APIException):
    def __init__(self, data):
        super().__init__(data)
        self.data = data


class ApplicationPartyMixin:
    def add_party(self, party):

        if self.case_type.id == CaseTypeEnum.EXHIBITION.id:
            raise ApplicationException({"bad_request": PartyErrors.BAD_CASE_TYPE})

        old_poa = None

        # Alternate behaviour of adding a party depending on party type
        if party.type == PartyType.ULTIMATE_END_USER:
            # Rule: Append
            pass
        elif party.type in [PartyType.END_USER, PartyType.CONSIGNEE]:
            # Rule: Replace
            old_poa = getattr(self, party.type)
            if old_poa:
                self.delete_party(old_poa)
        elif party.type == PartyType.THIRD_PARTY:
            # Rule: Append
            if not party.role:
                raise ApplicationException({"required": PartyErrors.ROLE["null"]})

        poa = PartyOnApplication.objects.create(application=self, party=party)

        return poa.party, old_poa.party if old_poa else None

    def get_party(self, party_pk):
        try:
            return self.active_parties.get(party=party_pk).party
        except PartyOnApplication.DoesNotExist:
            pass

    def delete_party(self, poa):
        poa.delete()

    def is_major_editable(self):
        return self.status.status == CaseStatusEnum.APPLICANT_EDITING or is_case_status_draft(self.status.status)

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
    def active_parties(self):
        return self.all_parties().filter(deleted_at__isnull=True)

    def all_parties(self):
        return self.parties.prefetch_related("party__flags").select_related(
            "party", "party__organisation", "party__country"
        )

    @property
    def consignee(self):
        """
        Backwards compatible
        Standard and HMRC Query applications
        """
        try:
            return self.active_parties.get(party__type=PartyType.CONSIGNEE)
        except PartyOnApplication.DoesNotExist:
            pass

    @property
    def end_user(self):
        """
        Backwards compatible
        Standard and HMRC Query applications
        """
        try:
            return self.active_parties.get(party__type=PartyType.END_USER)
        except PartyOnApplication.DoesNotExist:
            pass

    @property
    def ultimate_end_users(self):
        """
        Backwards compatible
        Standard and HMRC Query applications
        """
        return self.active_parties.filter(party__type=PartyType.ULTIMATE_END_USER)

    @property
    def third_parties(self):
        """
        Backwards compatible
        Standard and HMRC Query applications
        """
        return self.active_parties.filter(party__type=PartyType.THIRD_PARTY)


class BaseApplication(ApplicationPartyMixin, Case):
    name = models.TextField(default=None, blank=False, null=True)
    activity = models.TextField(default=None, blank=True, null=True)
    usage = models.TextField(default=None, blank=True, null=True)
    clearance_level = models.CharField(choices=PvGrading.choices, max_length=30, null=True)

    is_military_end_use_controls = models.BooleanField(blank=True, default=None, null=True)
    military_end_use_controls_ref = models.CharField(default=None, blank=True, null=True, max_length=255)

    is_informed_wmd = models.BooleanField(blank=True, default=None, null=True)
    informed_wmd_ref = models.CharField(default=None, blank=True, null=True, max_length=255)

    is_suspected_wmd = models.BooleanField(blank=True, default=None, null=True)
    suspected_wmd_ref = models.CharField(default=None, blank=True, null=True, max_length=2200)

    is_eu_military = models.BooleanField(blank=True, default=None, null=True)
    is_compliant_limitations_eu = models.BooleanField(blank=True, default=None, null=True)
    compliant_limitations_eu_ref = models.CharField(default=None, blank=True, null=True, max_length=2200)

    intended_end_use = models.CharField(default=None, blank=True, null=True, max_length=2200)
    agreed_to_foi = models.BooleanField(blank=True, default=None, null=True)

    objects = BaseApplicationManager()

    class Meta:
        ordering = ["created_at"]


# Licence Applications
class StandardApplication(BaseApplication):
    export_type = models.CharField(choices=ApplicationExportType.choices, default=None, max_length=50)
    reference_number_on_information_form = models.CharField(blank=True, null=True, max_length=255)
    have_you_been_informed = models.CharField(
        choices=ApplicationExportLicenceOfficialType.choices, blank=True, null=True, default=None, max_length=50,
    )
    is_shipped_waybill_or_lading = models.BooleanField(blank=True, default=None, null=True)
    non_waybill_or_lading_route_details = models.TextField(default=None, blank=True, null=True, max_length=2000)
    temp_export_details = models.CharField(blank=True, default=None, null=True, max_length=2200)
    is_temp_direct_control = models.BooleanField(blank=True, default=None, null=True)
    temp_direct_control_details = models.CharField(blank=True, default=None, null=True, max_length=2200)
    proposed_return_date = models.DateField(blank=True, null=True)
    trade_control_activity = models.CharField(
        choices=TradeControlActivity.choices, blank=False, null=True, max_length=100
    )
    trade_control_activity_other = models.CharField(blank=False, null=True, max_length=100)
    trade_control_product_categories = SeparatedValuesField(
        choices=TradeControlProductCategory.choices, blank=False, null=True, max_length=50
    )


class OpenApplication(BaseApplication):
    export_type = models.CharField(choices=ApplicationExportType.choices, default=None, max_length=50)
    is_shipped_waybill_or_lading = models.BooleanField(blank=True, default=None, null=True)
    non_waybill_or_lading_route_details = models.TextField(default=None, blank=True, null=True, max_length=2000)
    temp_export_details = models.CharField(blank=True, default=None, null=True, max_length=2200)
    is_temp_direct_control = models.BooleanField(blank=True, default=None, null=True)
    temp_direct_control_details = models.CharField(blank=True, default=None, null=True, max_length=2200)
    proposed_return_date = models.DateField(blank=True, null=True)
    trade_control_activity = models.CharField(
        choices=TradeControlActivity.choices, blank=False, null=True, max_length=100
    )
    trade_control_activity_other = models.CharField(blank=False, null=True, max_length=100)
    trade_control_product_categories = SeparatedValuesField(
        choices=TradeControlProductCategory.choices, blank=False, null=True, max_length=50
    )
    goodstype_category = models.CharField(choices=GoodsTypeCategory.choices, blank=False, null=True, max_length=100)
    contains_firearm_goods = models.BooleanField(blank=True, default=None, null=True)


# MOD Clearances Applications
# Exhibition includes End User, Consignee, Ultimate end users & Third parties
class ExhibitionClearanceApplication(BaseApplication):
    title = models.CharField(blank=False, null=True, max_length=255)
    first_exhibition_date = models.DateField(blank=False, null=True)
    required_by_date = models.DateField(blank=False, null=True)
    reason_for_clearance = models.TextField(default=None, blank=True, null=True, max_length=2000)


# Gifting includes End User & Third parties
class GiftingClearanceApplication(BaseApplication):
    pass


# F680 includes End User & Third parties
class F680ClearanceApplication(BaseApplication):
    types = models.ManyToManyField(F680ClearanceType, related_name="f680_clearance_application")

    expedited = models.NullBooleanField(default=None)
    expedited_date = models.DateField(null=True, default=None)

    foreign_technology = models.NullBooleanField(default=None)
    foreign_technology_description = models.CharField(max_length=2200, null=True)

    locally_manufactured = models.NullBooleanField(blank=True, default=None)
    locally_manufactured_description = models.CharField(max_length=2200, null=True)

    mtcr_type = models.CharField(choices=MTCRAnswers.choices, null=True, max_length=50)

    electronic_warfare_requirement = models.NullBooleanField(default=None)

    uk_service_equipment = models.NullBooleanField(default=None)
    uk_service_equipment_description = models.CharField(max_length=2200, null=True)
    uk_service_equipment_type = models.CharField(choices=ServiceEquipmentType.choices, null=True, max_length=50)

    prospect_value = models.DecimalField(max_digits=15, decimal_places=2, null=True)


# Queries
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


class AbstractGoodOnApplication(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_good_incorporated = models.BooleanField(null=True, blank=True, default=None)
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    comment = models.TextField(help_text="control review comment", default=None, blank=True, null=True)
    report_summary = models.TextField(default=None, blank=True, null=True)

    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE, null=False)
    control_list_entries = models.ManyToManyField(ControlListEntry)

    class Meta:
        abstract = True


class GoodOnApplication(AbstractGoodOnApplication):

    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE, related_name="goods", null=False)

    good = models.ForeignKey(Good, related_name="goods_on_application", on_delete=models.CASCADE)

    # Every application except Exhibition applications contains the following data, as a result these can be null
    quantity = models.FloatField(null=True, blank=True, default=None)
    unit = models.CharField(choices=Units.choices, max_length=50, null=True, blank=True, default=None)
    value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None)

    # Exhibition applications are the only applications that contain the following as such may be null
    item_type = models.CharField(choices=ItemType.choices, max_length=10, null=True, blank=True, default=None)
    other_item_type = models.CharField(max_length=100, null=True, blank=True, default=None)

    class Meta:
        ordering = ["created_at"]

    @property
    def description(self):
        return self.good.description


class CountryOnApplication(models.Model):
    """
    Open licence applications export to countries, instead of an end user
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(OpenApplication, related_name="application_countries", on_delete=models.CASCADE)
    country = models.ForeignKey(Country, related_name="countries_on_application", on_delete=models.CASCADE)
    contract_types = SeparatedValuesField(max_length=350, choices=ContractType.choices, null=True, default=None)
    other_contract_type_text = models.CharField(max_length=150, null=True, default=None)
    flags = models.ManyToManyField(Flag, related_name="countries_on_applications")


class PartyOnApplicationManager(models.Manager):
    def all(self):
        return self.get_queryset().exclude(party__type=PartyType.ADDITIONAL_CONTACT)

    def additional_contacts(self):
        return self.get_queryset().filter(party__type=PartyType.ADDITIONAL_CONTACT)


class PartyOnApplication(TimestampableModel):
    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE, related_name="parties")
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="parties_on_application")
    deleted_at = models.DateTimeField(null=True, default=None)

    objects = PartyOnApplicationManager()

    def __repr__(self):
        return str(
            {
                "application": self.application.id,
                "party_type": self.party.type,
                "deleted_at": self.deleted_at,
                "party_id": self.party.id,
            }
        )

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save()
