from django.db.models import Q
from rest_framework import serializers
from rest_framework.fields import CharField

from api.appeals.serializers import AppealSerializer
from api.applications.enums import (
    YesNoChoiceType,
    ApplicationExportLicenceOfficialType,
    ApplicationExportType,
    GoodsStartingPoint,
    GoodsRecipients,
)
from api.applications.mixins.serializers import PartiesSerializerMixin
from api.applications.models import StandardApplication
from api.licences.serializers.view_licence import CaseLicenceViewSerializer
from api.applications.serializers.serializer_helper import validate_field
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum
from api.cases.models import CaseType
from api.core.serializers import KeyValueChoiceField
from api.licences.models import Licence
from lite_content.lite_api import strings
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.statuses.serializers import CaseSubStatusSerializer
from api.staticdata.trade_control.enums import TradeControlProductCategory, TradeControlActivity

from .denial import DenialMatchOnApplicationViewSerializer
from .generic_application import (
    GenericApplicationListSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from .good import GoodOnApplicationViewSerializer
from .fields import CaseStatusField


class StandardApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    denial_matches = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    licence = serializers.SerializerMethodField()
    proposed_return_date = serializers.DateField(required=False)
    trade_control_activity = serializers.SerializerMethodField()
    trade_control_product_categories = serializers.SerializerMethodField()
    sanction_matches = serializers.SerializerMethodField()
    is_amended = serializers.SerializerMethodField()
    goods_starting_point = serializers.CharField()
    goods_recipients = serializers.CharField()
    appeal = AppealSerializer()
    sub_status = CaseSubStatusSerializer()

    class Meta:
        model = StandardApplication
        fields = (
            GenericApplicationViewSerializer.Meta.fields
            + PartiesSerializerMixin.Meta.fields
            + (
                "goods",
                "have_you_been_informed",
                "reference_number_on_information_form",
                "activity",
                "usage",
                "destinations",
                "denial_matches",
                "additional_documents",
                "is_military_end_use_controls",
                "military_end_use_controls_ref",
                "is_informed_wmd",
                "informed_wmd_ref",
                "is_suspected_wmd",
                "suspected_wmd_ref",
                "is_eu_military",
                "is_compliant_limitations_eu",
                "compliant_limitations_eu_ref",
                "intended_end_use",
                "licence",
                "is_shipped_waybill_or_lading",
                "non_waybill_or_lading_route_details",
                "temp_export_details",
                "is_temp_direct_control",
                "temp_direct_control_details",
                "proposed_return_date",
                "trade_control_activity",
                "trade_control_product_categories",
                "sanction_matches",
                "is_amended",
                "goods_starting_point",
                "goods_recipients",
                "is_mod_security_approved",
                "security_approvals",
                "f680_reference_number",
                "f1686_contracting_authority",
                "f1686_reference_number",
                "f1686_approval_date",
                "other_security_approval_details",
                "appeal_deadline",
                "appeal",
                "sub_status",
                "subject_to_itar_controls",
            )
        )

    def get_licence(self, instance):
        licence = Licence.objects.filter(case=instance).first()
        if licence:
            return CaseLicenceViewSerializer(licence).data

    def get_trade_control_activity(self, instance):
        key = instance.trade_control_activity
        value = (
            instance.trade_control_activity_other
            if key == TradeControlActivity.OTHER
            else TradeControlActivity.get_text(key)
        )
        return {"key": key, "value": value}

    def get_trade_control_product_categories(self, instance):
        trade_control_product_categories = (
            sorted(instance.trade_control_product_categories) if instance.trade_control_product_categories else []
        )
        return [
            {"key": tc_product_category, "value": TradeControlProductCategory.get_text(tc_product_category)}
            for tc_product_category in trade_control_product_categories
        ]

    def get_denial_matches(self, instance):
        denial_matches = instance.denial_matches.filter(denial_entity__denial__is_revoked=False)
        return DenialMatchOnApplicationViewSerializer(denial_matches, many=True).data

    def get_is_amended(self, instance):
        """Determines whether an application is major/minor edited using Audit logs
        and returns True if either of the amends are done, False otherwise"""
        audit_qs = Audit.objects.filter(target_object_id=instance.id)
        is_reference_name_updated = audit_qs.filter(verb=AuditType.UPDATED_APPLICATION_NAME).exists()
        is_product_removed = audit_qs.filter(verb=AuditType.REMOVE_GOOD_FROM_APPLICATION).exists()
        app_letter_ref_updated = audit_qs.filter(
            Q(
                verb__in=[
                    AuditType.ADDED_APPLICATION_LETTER_REFERENCE,
                    AuditType.UPDATE_APPLICATION_LETTER_REFERENCE,
                    AuditType.REMOVED_APPLICATION_LETTER_REFERENCE,
                ]
            )
        )
        # in case of doing major edits then the status is set as "Applicant editing"
        # Here we are detecting the transition from "Submitted" -> "Applicant editing"
        for item in audit_qs.filter(verb=AuditType.UPDATED_STATUS):
            status = item.payload["status"]
            if status["old"] == CaseStatusEnum.get_text(CaseStatusEnum.SUBMITTED) and status[
                "new"
            ] == CaseStatusEnum.get_text(CaseStatusEnum.APPLICANT_EDITING):
                return True

        return any([is_reference_name_updated, app_letter_ref_updated, is_product_removed])


class StandardApplicationDataWorkspaceSerializer(serializers.ModelSerializer):
    is_amended = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    export_type = serializers.SerializerMethodField()
    case_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    organisation = serializers.SerializerMethodField()
    submitted_by = serializers.SerializerMethodField()
    superseded_by = serializers.SerializerMethodField()
    amendment_of = serializers.SerializerMethodField()
    case_officer = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "created_at",
            "updated_at",
            "export_type",
            "reference_code",
            "submitted_at",
            "name",
            "activity",
            "is_eu_military",
            "is_informed_wmd",
            "is_suspected_wmd",
            "is_compliant_limitations_eu",
            "is_military_end_use_controls",
            "intended_end_use",
            "agreed_to_foi",
            "foi_reason",
            "reference_number_on_information_form",
            "have_you_been_informed",
            "is_shipped_waybill_or_lading",
            "is_temp_direct_control",
            "proposed_return_date",
            "sla_days",
            "sla_remaining_days",
            "sla_updated_at",
            "last_closed_at",
            "submitted_by",
            "status",
            "case_type",
            "organisation",
            "case_officer",
            "copy_of",
            "is_amended",
            "destinations",
            "goods_starting_point",
            "amendment_of",
            "superseded_by",
        )

    def get_is_amended(self, instance):
        """Determines whether an application is major/minor edited using Audit logs
        and returns True if either of the amends are done, False otherwise"""
        is_reference_name_updated = bool(instance.is_reference_update_audits)
        is_product_removed = bool(instance.is_product_removed_audits)
        app_letter_ref_updated = bool(instance.app_letter_ref_updated_audits)
        # in case of doing major edits then the status is set as "Applicant editing"
        # Here we are detecting the transition from "Submitted" -> "Applicant editing"
        for item in instance.updated_status_audits:
            status = item.payload["status"]
            if status["old"] == CaseStatusEnum.get_text(CaseStatusEnum.SUBMITTED) and status[
                "new"
            ] == CaseStatusEnum.get_text(CaseStatusEnum.APPLICANT_EDITING):
                return True

        return any([is_reference_name_updated, app_letter_ref_updated, is_product_removed])

    def get_destinations(self, application):
        if not application.end_users:
            return {"data": ""}

        end_user = application.end_users[0]
        return {"data": {"country": {"id": end_user.party.country_id}}}

    def get_export_type(self, application):
        if hasattr(application, "export_type"):
            return {
                "key": application.export_type,
            }

    def get_status(self, application):
        return {
            "id": application.status_id,
        }

    def get_case_type(self, application):
        return {
            "id": application.case_type_id,
        }

    def get_organisation(self, application):
        return {
            "id": application.organisation_id,
        }

    def get_submitted_by(self, application):
        return (
            f"{application.submitted_by.first_name} {application.submitted_by.last_name}"
            if application.submitted_by
            else ""
        )

    def get_superseded_by(self, application):
        if not application.superseded_by:
            return None
        return str(application.superseded_by.pk)

    def get_amendment_of(self, application):
        if not application.amendment_of_id:
            return None
        return str(application.amendment_of_id)

    def get_case_officer(self, application):
        if not application.case_officer_id:
            return None
        return {
            "id": application.case_officer_id,
        }


class StandardApplicationCreateSerializer(serializers.ModelSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Applications.Generic.MISSING_REFERENCE_NAME_ERROR},
    )
    export_type = KeyValueChoiceField(choices=ApplicationExportType.choices, required=False)
    have_you_been_informed = KeyValueChoiceField(
        choices=ApplicationExportLicenceOfficialType.choices,
        error_messages={"required": strings.Goods.INFORMED},
    )
    reference_number_on_information_form = CharField(allow_blank=True)

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "name",
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
        )

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        validated_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT)
        validated_data["case_type"] = CaseType.objects.get(pk=CaseTypeEnum.SIEL.id)
        return super().create(validated_data)

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs["child"] = GenericApplicationListSerializer()
        return serializers.ListSerializer(*args, **kwargs)


class StandardApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    export_type = KeyValueChoiceField(
        choices=ApplicationExportType.choices, required=False, allow_blank=True, allow_null=True
    )
    goods_starting_point = KeyValueChoiceField(choices=GoodsStartingPoint.choices, required=False, allow_blank=True)
    goods_recipients = KeyValueChoiceField(choices=GoodsRecipients.choices, required=False, allow_blank=True)
    reference_number_on_information_form = CharField(max_length=100, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = StandardApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + (
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "is_shipped_waybill_or_lading",
            "non_waybill_or_lading_route_details",
            "goods_starting_point",
            "goods_recipients",
            "is_mod_security_approved",
            "security_approvals",
            "f680_reference_number",
            "f1686_contracting_authority",
            "f1686_reference_number",
            "f1686_approval_date",
            "other_security_approval_details",
            "subject_to_itar_controls",
        )

    def __init__(self, *args, **kwargs):
        super(StandardApplicationUpdateSerializer, self).__init__(*args, **kwargs)

        if self.get_initial().get("is_shipped_waybill_or_lading") == "True":
            if hasattr(self, "initial_data"):
                self.initial_data["non_waybill_or_lading_route_details"] = None

        if self.instance.case_type.id == CaseTypeEnum.SICL.id:
            self.fields.pop("have_you_been_informed")
            self.fields.pop("reference_number_on_information_form")

    def update(self, instance, validated_data):
        self._update_have_you_been_informed_linked_fields(instance, validated_data)

        instance = super().update(instance, validated_data)
        return instance

    @classmethod
    def _update_have_you_been_informed_linked_fields(cls, instance, validated_data):
        instance.have_you_been_informed = validated_data.pop("have_you_been_informed", instance.have_you_been_informed)

        reference_number_on_information_form = validated_data.pop(
            "reference_number_on_information_form",
            instance.reference_number_on_information_form,
        )

        if instance.have_you_been_informed == YesNoChoiceType.YES:
            instance.reference_number_on_information_form = reference_number_on_information_form
        else:
            instance.reference_number_on_information_form = None

    def validate(self, data):
        validated_data = super().validate(data)
        validate_field(
            validated_data,
            "goods_starting_point",
            "Select if the products will begin their export journey in Great Britain or Northern Ireland",
        )
        validate_field(
            validated_data,
            "export_type",
            strings.Applications.Generic.NO_EXPORT_TYPE,
        )
        validate_field(
            validated_data,
            "is_shipped_waybill_or_lading",
            strings.Applications.Generic.RouteOfGoods.IS_SHIPPED_AIR_WAY_BILL_OR_LADING,
        )
        if validated_data.get("is_shipped_waybill_or_lading") is False:
            validate_field(
                validated_data,
                "non_waybill_or_lading_route_details",
                strings.Applications.Generic.RouteOfGoods.SHIPPING_DETAILS,
                required=True,
            )
        validate_field(
            validated_data,
            "goods_recipients",
            "Select who the products are going to",
        )
        return validated_data


class StandardApplicationRequiresSerialNumbersSerializer(
    PartiesSerializerMixin,
    serializers.ModelSerializer,
):
    goods = serializers.SerializerMethodField()
    status = CaseStatusField()

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "name",
            "reference_code",
            "goods",
            "status",
        ) + PartiesSerializerMixin.Meta.fields

    def get_goods(self, instance):
        return [{"good": {"name": good_on_application.good.name}} for good_on_application in instance.goods.all()]
