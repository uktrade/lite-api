import logging
import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework.exceptions import APIException
from separatedvaluesfield.models import SeparatedValuesField

from api.applications.enums import (
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
    SecurityClassifiedApprovalsType,
    NSGListType,
)
from api.appeals.models import Appeal
from api.applications.exceptions import AmendmentError
from api.applications.managers import BaseApplicationManager
from api.applications.libraries.application_helpers import create_submitted_audit
from api.audit_trail.models import AuditType
from api.audit_trail import service as audit_trail_service
from api.cases.enums import CaseTypeEnum
from api.cases.models import Case, CaseQueue
from api.common.models import TimestampableModel
from api.core.model_mixins import Clonable
from api.documents.models import Document
from api.external_data.models import DenialEntity
from api.external_data import enums as denial_enums
from api.flags.models import Flag
from api.goods.enums import ItemType, PvGrading
from api.goods.models import Good
from api.organisations.enums import OrganisationDocumentType
from api.organisations.models import Site, ExternalLocation
from api.parties.enums import PartyType
from api.parties.models import Party
from api.queues.models import Queue
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.denial_reasons.models import DenialReason
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.report_summaries.models import ReportSummary, ReportSummaryPrefix, ReportSummarySubject
from api.staticdata.statuses.enums import CaseStatusEnum, CaseStatusIdEnum, CaseSubStatusIdEnum
from api.staticdata.statuses.libraries.case_status_validate import is_case_status_draft
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.trade_control.enums import TradeControlProductCategory, TradeControlActivity
from api.staticdata.units.enums import Units
from api.users.enums import SystemUser
from api.users.models import ExporterUser, GovUser, BaseUser
from lite_content.lite_api.strings import PartyErrors

from lite_routing.routing_rules_internal.enums import QueuesEnum


logger = logging.getLogger(__name__)


class ApplicationException(APIException):
    def __init__(self, data):
        super().__init__(data)
        self.data = data


class ApplicationPartyMixin:
    def add_party(self, party):
        if self.case_type.id == CaseTypeEnum.EXHIBITION.id:
            raise ApplicationException({"bad_request": PartyErrors.BAD_CASE_TYPE})

        old_party_on_application = None

        # Alternate behaviour of adding a party depending on party type
        if party.type == PartyType.ULTIMATE_END_USER:
            # Rule: Append
            pass
        elif party.type in [PartyType.END_USER, PartyType.CONSIGNEE]:
            # Rule: Replace
            old_party_on_application = getattr(self, party.type)
            if old_party_on_application:
                self.delete_party(old_party_on_application)
        elif party.type == PartyType.THIRD_PARTY:
            # Rule: Append
            if not party.role:
                raise ApplicationException({"required": PartyErrors.ROLE["null"]})

        party_on_application = PartyOnApplication.objects.create(application=self, party=party)

        return party_on_application.party, old_party_on_application.party if old_party_on_application else None

    def get_party(self, party_pk):
        try:
            return self.active_parties.get(party=party_pk).party
        except PartyOnApplication.DoesNotExist:
            pass

    def delete_party(self, party_on_application):
        # delete party if application not submitted else 'expire' party
        if self.status.status == CaseStatusEnum.DRAFT:
            party_on_application.delete(is_draft=True)
        else:
            party_on_application.delete()

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
        return self.all_parties.filter(deleted_at__isnull=True)

    @cached_property
    def all_parties(self):
        return self.parties.prefetch_related(
            "party__flags",
            "party__flags__team",
            "party__partydocument_set",
            "party__parties_on_application",
            "party__parties_on_application__flags",
        ).select_related(
            "party",
            "party__organisation",
            "party__country",
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
            return self.active_parties.filter(party__type=PartyType.END_USER).first()
        except PartyOnApplication.DoesNotExist:
            pass

    @property
    def end_users(self):
        try:
            return self.active_parties.filter(party__type=PartyType.END_USER)
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
    foi_reason = models.TextField(blank=True, default="")

    appeal = models.OneToOneField(Appeal, blank=True, null=True, on_delete=models.SET_NULL)
    appeal_deadline = models.DateTimeField(
        blank=True, null=True, default=None, help_text="Date before which Exporter can initiate an appeal on a refusal"
    )

    objects = BaseApplicationManager()

    class Meta:
        ordering = ["created_at"]

    def on_submit(self, old_status):
        additional_payload = {}
        if self.amendment_of:
            # Add an audit entry to the case that was superseded by this amendment
            audit_trail_service.create_system_user_audit(
                verb=AuditType.EXPORTER_SUBMITTED_AMENDMENT,
                target=self.amendment_of,
                payload={
                    "amendment": {"reference_code": self.reference_code},
                },
            )
            additional_payload["amendment_of"] = {"reference_code": self.amendment_of.reference_code}
        create_submitted_audit(self.submitted_by, self, old_status, additional_payload)

    def add_to_queue(self, queue):
        case = self.get_case()

        self.queues.add(queue)

        audit_trail_service.create_system_user_audit(
            verb=AuditType.MOVE_CASE,
            target=case,
            payload={
                "queues": [queue.name],
                "queue_ids": [str(queue.id)],
                "case_status": case.status.status,
            },
        )

    def set_status(self, status):
        case = self.get_case()

        old_status = self.status
        self.status = get_case_status_by_status(status)

        audit_trail_service.create_system_user_audit(
            verb=AuditType.UPDATED_STATUS,
            target=case,
            payload={
                "status": {
                    "new": self.status.status,
                    "old": old_status.status,
                },
            },
        )

        self.save()

    def set_appealed(self, appeal, exporter_user):
        self.appeal = appeal
        self.save()

        audit_trail_service.create(
            actor=exporter_user,
            verb=AuditType.EXPORTER_APPEALED_REFUSAL,
            target=self.get_case(),
            payload={},
        )

        self.set_status(CaseStatusEnum.UNDER_APPEAL)
        self.set_sub_status(CaseSubStatusIdEnum.UNDER_APPEAL__APPEAL_RECEIVED)
        self.add_to_queue(Queue.objects.get(id=QueuesEnum.LU_APPEALS))

    def create_amendment(self, user):
        raise NotImplementedError()


# Licence     Applications
class StandardApplication(BaseApplication, Clonable):
    GB = "GB"
    NI = "NI"
    GOODS_STARTING_POINT_CHOICES = [
        (GB, "Great Britain"),
        (NI, "Northern Ireland"),
    ]
    DIRECT_TO_END_USER = "direct_to_end_user"
    VIA_CONSIGNEE = "via_consignee"
    VIA_CONSIGNEE_AND_THIRD_PARTIES = "via_consignee_and_third_parties"

    GOODS_RECIPIENTS_CHOICES = [
        (DIRECT_TO_END_USER, "Directly to the end-user"),
        (VIA_CONSIGNEE, "To an end-user via a consignee"),
        (VIA_CONSIGNEE_AND_THIRD_PARTIES, "To an end-user via a consignee, with additional third parties"),
    ]

    export_type = models.TextField(choices=ApplicationExportType.choices, blank=True, default="")
    reference_number_on_information_form = models.CharField(blank=True, null=True, max_length=255)
    have_you_been_informed = models.CharField(
        choices=ApplicationExportLicenceOfficialType.choices,
        blank=True,
        null=True,
        default=None,
        max_length=50,
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
    goods_recipients = models.TextField(choices=GOODS_RECIPIENTS_CHOICES, default="")
    goods_starting_point = models.TextField(choices=GOODS_STARTING_POINT_CHOICES, default="")

    # MOD Security approval fields
    is_mod_security_approved = models.BooleanField(blank=True, default=None, null=True)
    security_approvals = ArrayField(
        models.CharField(choices=SecurityClassifiedApprovalsType.choices, max_length=255), blank=True, null=True
    )
    f680_reference_number = models.CharField(default=None, blank=True, null=True, max_length=100)
    f1686_contracting_authority = models.CharField(default=None, blank=True, null=True, max_length=200)
    f1686_reference_number = models.CharField(default=None, blank=True, null=True, max_length=100)
    f1686_approval_date = models.DateField(blank=False, null=True)
    other_security_approval_details = models.TextField(default=None, blank=True, null=True)
    subject_to_itar_controls = models.BooleanField(blank=True, default=None, null=True)

    clone_exclusions = [
        "appeal",
        "appeal_deadline",
        "id",
        "flags",
        "queues",
        "reference_code",
        "submitted_at",
        "submitted_by",
        "status",
        "sub_status",
        "case_officer",
        "copy_of",
        "amendment_of",
        "sla_days",
        "sla_remaining_days",
        "sla_updated_at",
        "additional_contacts",
        "case_ptr",
        "baseapplication_ptr",
        "last_closed_at",
    ]
    clone_mappings = {
        "organisation": "organisation_id",
        "case_type": "case_type_id",
    }
    clone_overrides = {
        "status_id": CaseStatusIdEnum.DRAFT,
    }

    def clone(self, exclusions=None, **overrides):
        cloned_application = super().clone(exclusions=exclusions, **overrides)

        application_documents = ApplicationDocument.objects.filter(application=self, safe=True)
        for application_document in application_documents:
            application_document.clone(application=cloned_application)

        site_on_applications = SiteOnApplication.objects.filter(application=self)
        for site_on_application in site_on_applications:
            site_on_application.clone(application=cloned_application)

        good_on_applications = GoodOnApplication.objects.filter(application=self)
        for good_on_application in good_on_applications:
            good_on_application.clone(application=cloned_application)

        party_on_applications = PartyOnApplication.objects.filter(application=self)
        for party_on_application in party_on_applications:
            party_on_application.clone(application=cloned_application)

        return cloned_application

    @transaction.atomic
    def create_amendment(self, user):
        # It's possible that we've arrived here multiple times simultaneously because multiple requests to create an
        # amendment have been made at the same time.
        # The views that call this may have already checked the status but it's possible that when they checked it was
        # before the status has actually been updated on the application so we've got a potential race condition going.
        # What we want to do here is lock the row to make sure that only one request can be trying to create an
        # amendment at any one time and if we have multiple requests clashing we'll re-check the status once the lock
        # has been removed from any other racing requests.
        # To be helpful to the caller we'll return the amendment that did happen even if there are multiple requests.
        original = StandardApplication.objects.select_for_update().get(pk=self.pk)
        if not CaseStatusEnum.can_invoke_major_edit(original.status.status):
            logger.warning(
                "Attempted to create an amendment from an already amended application %s with status %s",
                original.pk,
                original.status,
            )
            if original.superseded_by:
                logger.info(
                    "Found an amendment already: %s for the application: %s",
                    original.superseded_by.pk,
                    original.pk,
                )
                return StandardApplication.objects.get(pk=original.superseded_by.pk)
            raise AmendmentError(f"Failed to create an amendment from {original.pk}")

        amendment_application = self.clone(amendment_of=self)
        CaseQueue.objects.filter(case=self.case_ptr).delete()
        audit_trail_service.create(
            actor=user,
            verb=AuditType.EXPORTER_CREATED_AMENDMENT,
            target=self.get_case(),
            payload={},
        )
        audit_trail_service.create_system_user_audit(
            verb=AuditType.AMENDMENT_CREATED,
            target=amendment_application.case_ptr,
            payload={"superseded_case": {"reference_code": self.reference_code}},
            ignore_case_status=True,
        )
        system_user = BaseUser.objects.get(id=SystemUser.id)
        self.case_ptr.change_status(system_user, get_case_status_by_status(CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT))
        return amendment_application


class ApplicationDocument(Document, Clonable):
    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE)
    description = models.TextField(default=None, blank=True, null=True)
    document_type = models.TextField(
        choices=OrganisationDocumentType.choices,
        default=None,
        blank=True,
        null=True,
    )

    clone_exclusions = [
        "id",
        "application",
        "document_ptr",
    ]


class SiteOnApplication(models.Model, Clonable):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, related_name="sites_on_application", on_delete=models.CASCADE)
    application = models.ForeignKey(BaseApplication, related_name="application_sites", on_delete=models.CASCADE)

    clone_exclusions = [
        "id",
        "application",
    ]
    clone_mappings = {
        "site": "site_id",
    }


class ApplicationDenialReason(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        BaseApplication,
        related_name="application_denial_reason",
        on_delete=models.CASCADE,
    )
    reasons = models.ManyToManyField(DenialReason)
    reason_details = models.TextField(default=None, blank=True, null=True, max_length=2200)


class ExternalLocationOnApplication(models.Model, Clonable):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_location = models.ForeignKey(
        ExternalLocation,
        related_name="external_locations_on_application",
        on_delete=models.CASCADE,
    )
    application = models.ForeignKey(
        BaseApplication,
        related_name="external_application_sites",
        on_delete=models.CASCADE,
    )

    clone_exclusions = [
        "id",
        "application",
    ]
    clone_mappings = {
        "external_location": "external_location_id",
    }


class AbstractGoodOnApplication(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_good_incorporated = models.BooleanField(null=True, blank=True, default=None)
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    comment = models.TextField(help_text="control review comment", default=None, blank=True, null=True)
    # DEPRECATED: We should remove this after checking that report_summaries supersedes it (including data)
    report_summary = models.TextField(default=None, blank=True, null=True)
    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE, null=False)
    control_list_entries = models.ManyToManyField(ControlListEntry)
    end_use_control = ArrayField(
        models.TextField(),
        default=list,
        help_text="Control code given to good due to the end use e.g, a wood screw may be used in a Harrier jump jet.",
        blank=True,
    )
    firearm_details = models.ForeignKey(
        "goods.FirearmGoodDetails", on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    is_precedent = models.BooleanField(blank=False, default=False)

    class Meta:
        abstract = True


class GoodOnApplicationControlListEntry(models.Model):
    goodonapplication = models.ForeignKey("GoodOnApplication", related_name="goods", on_delete=models.CASCADE)
    controllistentry = models.ForeignKey(ControlListEntry, related_name="controllistentry", on_delete=models.CASCADE)

    class Meta:
        """
        This table name should not be modified, this is the through table name that Django created for us
        when previously 'through' table was not specified for the M2M field 'control_list_entries' in
        'GoodOnApplication' model below. We have recently updated the field to use this model as the
        through table and we don't want Django to create a new table but use the previously inferred
        through table instead hence we are specifying the same table name using the 'db_table' attribute.
        """

        db_table = "applications_goodonapplication_control_list_entries"


class GoodOnApplicationRegimeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good_on_application = models.ForeignKey(
        "GoodOnApplication",
        on_delete=models.CASCADE,
        related_name="good_on_applications",
    )
    regime_entry = models.ForeignKey(
        RegimeEntry,
        on_delete=models.CASCADE,
        related_name="regime_entries",
    )


class GoodOnApplication(AbstractGoodOnApplication, Clonable):
    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE, related_name="goods", null=False)

    good = models.ForeignKey(Good, related_name="goods_on_application", on_delete=models.CASCADE)

    # Every application except Exhibition applications contains the following data, as a result these can be null
    quantity = models.FloatField(null=True, blank=True, default=None)
    unit = models.CharField(choices=Units.choices, max_length=50, null=True, blank=True, default=None)
    value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None)

    # DEPRECATED: we should remove this after checking report_summaries fully supersedes this (including legacy data)
    report_summary_prefix = models.ForeignKey(
        ReportSummaryPrefix, on_delete=models.PROTECT, blank=True, null=True, related_name="prefix_good_on_application"
    )
    # DEPRECATED: we should remove this after checking report_summaries fully supersedes this (including legacy data)
    report_summary_subject = models.ForeignKey(
        ReportSummarySubject,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="subject_good_on_application",
    )
    # report_summaries supersedes report_summary_subject and report_summary_prefix
    report_summaries = models.ManyToManyField(ReportSummary, related_name="goods_on_application")

    # Exhibition applications are the only applications that contain the following as such may be null
    item_type = models.CharField(choices=ItemType.choices, max_length=10, null=True, blank=True, default=None)
    other_item_type = models.CharField(max_length=100, null=True, blank=True, default=None)
    control_list_entries = models.ManyToManyField(ControlListEntry, through=GoodOnApplicationControlListEntry)
    regime_entries = models.ManyToManyField(RegimeEntry, through=GoodOnApplicationRegimeEntry)

    # Onward export
    is_onward_exported = models.BooleanField(default=None, blank=True, null=True)
    is_onward_altered_processed = models.BooleanField(default=None, blank=True, null=True)
    is_onward_altered_processed_comments = models.TextField(
        default="", blank=True, null=True, help_text="How the product will be processed or altered"
    )
    is_onward_incorporated = models.BooleanField(default=None, blank=True, null=True)
    is_onward_incorporated_comments = models.TextField(
        default="", blank=True, null=True, help_text="what's being incorporated into the product"
    )

    # Trigger list fields
    nsg_list_type = models.CharField(choices=NSGListType.choices, max_length=32, blank=True, default="")
    is_trigger_list_guidelines_applicable = models.BooleanField(
        default=None, blank=True, null=True, help_text="Do the trigger list guidelines apply to this product?"
    )
    is_nca_applicable = models.BooleanField(default=None, blank=True, null=True)
    nsg_assessment_note = models.TextField(help_text="Trigger list assessment note", default="", blank=True)
    is_ncsc_military_information_security = models.BooleanField(
        default=None, blank=True, null=True, help_text="trigger to NCSC for a recommendation"
    )

    assessment_date = models.DateTimeField(blank=True, null=True)
    assessed_by = models.ForeignKey(
        GovUser, on_delete=models.DO_NOTHING, blank=True, null=True, related_name="assessed_by"
    )

    clone_exclusions = [
        "id",
        "application",
        "control_list_entries",
        "is_good_controlled",
        "regime_entries",
        "report_summary",
        "report_summaries",
        "report_summary_prefix",
        "report_summary_subject",
        "assessed_by",
        "assessment_date",
        "comment",
        "firearm_details",
        "audit_trail",
        "is_trigger_list_guidelines_applicable",
        "nsg_assessment_note",
        "nsg_list_type",
    ]
    clone_mappings = {
        "good": "good_id",
    }

    def clone(self, exclusions=None, **overrides):
        cloned_good_on_application = super().clone(exclusions=exclusions, **overrides)
        if self.firearm_details:
            cloned_good_on_application.firearm_details = self.firearm_details.clone()
            cloned_good_on_application.save()

        good_on_application_documents = GoodOnApplicationDocument.objects.filter(good_on_application=self, safe=True)
        for good_on_application_document in good_on_application_documents:
            good_on_application_document.clone(
                good_on_application=cloned_good_on_application, application=overrides["application"]
            )

        good_on_application_internal_documents = GoodOnApplicationInternalDocument.objects.filter(
            good_on_application=self,
            safe=True,
        )
        for good_on_application_internal_document in good_on_application_internal_documents:
            good_on_application_internal_document.clone(good_on_application=cloned_good_on_application)

        return cloned_good_on_application

    class Meta:
        ordering = ["created_at"]

    @property
    def name(self):
        return self.good.name

    @property
    def description(self):
        return self.good.description

    def get_control_list_entries(self):
        """
        returns relevant control list entries, they can either exist at this level
        or if not overridden then at the good level
        """
        if self.is_good_controlled is None:
            return self.good.control_list_entries
        return self.control_list_entries


class GoodOnApplicationDocument(Document, Clonable):
    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE, related_name="goods_document")
    good = models.ForeignKey(Good, related_name="goods_on_application_document", on_delete=models.CASCADE)
    user = models.ForeignKey(ExporterUser, on_delete=models.DO_NOTHING, related_name="user")
    document_type = models.TextField(
        choices=OrganisationDocumentType.choices,
        default=None,
        blank=True,
        null=True,
    )
    # Joining on good_on_application may seem a little redundant because we are already linking to both the application
    # and the good on this model, however, because the relationship between application and good is many-to-many just
    # joining against them on this model means it is ambiguous as to exactly which one of the goods on the application
    # this may be referring to (a good could be attached to the same application many times).
    # Attaching to GoodOnApplication makes it explicit which good (if there are many) this document refers to.
    # We have to keep this null and can't just replace this relationship with `good` and `application` as we can't
    # unambiguously go back and know exactly what one of the many possible goods on the application the document refers
    # to.
    good_on_application = models.ForeignKey(GoodOnApplication, on_delete=models.CASCADE, blank=True, null=True)

    clone_exclusions = [
        "id",
        "good_on_application",
        "application",
        "document_ptr",
    ]
    clone_mappings = {
        "good": "good_id",
        "user": "user_id",
    }


class GoodOnApplicationInternalDocument(Document, Clonable):
    document_title = models.TextField(
        default="",
        blank=True,
        null=True,
    )
    good_on_application = models.ForeignKey(
        GoodOnApplication, on_delete=models.CASCADE, related_name="good_on_application_internal_documents"
    )

    clone_exclusions = [
        "id",
        "good_on_application",
        "document_ptr",
    ]


class PartyOnApplicationManager(models.Manager):
    def all(self):
        return self.get_queryset().exclude(party__type=PartyType.ADDITIONAL_CONTACT)

    def additional_contacts(self):
        return self.get_queryset().filter(party__type=PartyType.ADDITIONAL_CONTACT)


class PartyOnApplication(TimestampableModel, Clonable):
    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE, related_name="parties")
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="parties_on_application")
    deleted_at = models.DateTimeField(null=True, default=None)
    flags = models.ManyToManyField(Flag, related_name="parties_on_application")

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
        if kwargs.get("is_draft", False):
            super().delete()
        else:
            self.deleted_at = timezone.now()
            self.save()

    clone_exclusions = [
        "id",
        "application",
        "flags",
        "party",
    ]

    def clone(self, exclusions=None, **overrides):
        if not overrides.get("party"):
            cloned_party = self.party.clone()
            overrides["party"] = cloned_party
        return super().clone(exclusions=exclusions, **overrides)


class DenialMatchOnApplication(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(BaseApplication, on_delete=models.CASCADE, related_name="denial_matches")
    denial_entity = models.ForeignKey(
        DenialEntity, related_name="denial_matches_on_application", on_delete=models.CASCADE
    )
    category = models.TextField(choices=denial_enums.DenialMatchCategory.choices)
