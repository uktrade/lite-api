from django.db.models import Q
from rest_framework import serializers
from rest_framework.fields import CharField

from api.applications.enums import (
    YesNoChoiceType,
    ApplicationExportLicenceOfficialType,
    ApplicationExportType,
    GoodsStartingPoint,
    GoodsRecipients,
)
from api.applications.mixins.serializers import PartiesSerializerMixin
from api.applications.models import DenialMatchOnApplication, StandardApplication
from api.licences.serializers.view_licence import CaseLicenceViewSerializer
from api.applications.serializers.serializer_helper import validate_field
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum
from api.core.serializers import KeyValueChoiceField
from api.licences.models import Licence
from lite_content.lite_api import strings
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.trade_control.enums import TradeControlProductCategory, TradeControlActivity

from .denial import DenialMatchOnApplicationViewSerializer
from .generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from .good import GoodOnApplicationViewSerializer
from .fields import CaseStatusField


# ~550ms overall..
#   PartiesSerializerMixin; ~200ms
class StandardApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)  # ~50ms
    destinations = serializers.SerializerMethodField()  # ~50ms
    denial_matches = serializers.SerializerMethodField()  # ~100ms
    additional_documents = serializers.SerializerMethodField()  # ~50ms
    licence = serializers.SerializerMethodField()  # ~50ms
    proposed_return_date = serializers.DateField(required=False)
    trade_control_activity = serializers.SerializerMethodField()
    trade_control_product_categories = serializers.SerializerMethodField()
    sanction_matches = serializers.SerializerMethodField()
    is_amended = serializers.SerializerMethodField()  # ~100ms
    goods_starting_point = serializers.CharField()
    goods_recipients = serializers.CharField()

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
        denial_matches = instance.denial_matches.filter(denial__is_revoked=False)
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


class StandardApplicationCreateSerializer(GenericApplicationCreateSerializer):
    export_type = KeyValueChoiceField(choices=ApplicationExportType.choices, required=False)
    have_you_been_informed = KeyValueChoiceField(
        choices=ApplicationExportLicenceOfficialType.choices,
        error_messages={"required": strings.Goods.INFORMED},
    )
    reference_number_on_information_form = CharField(allow_blank=True)
    trade_control_activity = KeyValueChoiceField(
        choices=TradeControlActivity.choices,
        error_messages={"required": strings.Applications.Generic.TRADE_CONTROL_ACTIVITY_ERROR},
    )
    trade_control_activity_other = CharField(
        error_messages={
            "blank": strings.Applications.Generic.TRADE_CONTROL_ACTIVITY_OTHER_ERROR,
            "required": strings.Applications.Generic.TRADE_CONTROL_ACTIVITY_OTHER_ERROR,
        }
    )
    trade_control_product_categories = serializers.MultipleChoiceField(
        choices=TradeControlProductCategory.choices,
        error_messages={"required": strings.Applications.Generic.TRADE_CONTROl_PRODUCT_CATEGORY_ERROR},
    )

    class Meta:
        model = StandardApplication
        fields = GenericApplicationCreateSerializer.Meta.fields + (
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "trade_control_activity",
            "trade_control_activity_other",
            "trade_control_product_categories",
        )

    def __init__(self, case_type_id, **kwargs):
        super().__init__(case_type_id, **kwargs)
        self.trade_control_licence = case_type_id in [str(CaseTypeEnum.SICL.id), str(CaseTypeEnum.OICL.id)]

        # Remove fields from serializer depending on the application being for a Trade Control Licence
        if self.trade_control_licence:
            self.fields.pop("export_type")
            self.fields.pop("have_you_been_informed")
            self.fields.pop("reference_number_on_information_form")

            if not self.initial_data.get("trade_control_activity") == TradeControlActivity.OTHER:
                self.fields.pop("trade_control_activity_other")
        else:
            self.fields.pop("trade_control_activity")
            self.fields.pop("trade_control_activity_other")
            self.fields.pop("trade_control_product_categories")

    def create(self, validated_data):
        # Trade Control Licences are always permanent
        if self.trade_control_licence:
            validated_data["export_type"] = ApplicationExportType.PERMANENT

        return super().create(validated_data)


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
