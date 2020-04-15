from rest_framework import serializers
from rest_framework.fields import CharField

from applications.enums import (
    GoodsCategory,
    YesNoChoiceType,
    ApplicationExportLicenceOfficialType,
    ApplicationExportType,
    TradeControlActivity,
    TradeControlProductCategory,
)
from applications.mixins.serializers import PartiesSerializerMixin
from applications.models import StandardApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from applications.serializers.good import GoodOnApplicationViewSerializer
from applications.serializers.serializer_helper import validate_field
from cases.enums import CaseTypeEnum
from conf.serializers import KeyValueChoiceField
from licences.models import Licence
from licences.serializers import CaseLicenceViewSerializer
from lite_content.lite_api import strings


class StandardApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    goods_categories = serializers.SerializerMethodField()
    licence = serializers.SerializerMethodField()
    proposed_return_date = serializers.DateField(required=False)
    tc_activity = serializers.SerializerMethodField()
    tc_product_category = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        fields = (
            GenericApplicationViewSerializer.Meta.fields
            + PartiesSerializerMixin.Meta.fields
            + (
                "goods",
                "have_you_been_informed",
                "reference_number_on_information_form",
                "goods_categories",
                "activity",
                "usage",
                "destinations",
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
                "tc_activity",
                "tc_product_category",
            )
        )

    def get_licence(self, instance):
        licence = Licence.objects.filter(application=instance).first()
        return CaseLicenceViewSerializer(licence).data

    def get_goods_categories(self, instance):
        # Return a formatted key, value format of GoodsCategories
        # Order according to the choices in GoodsCategory
        return_value = [{"key": x, "value": GoodsCategory.get_text(x)} for x in instance.goods_categories or []]
        return sorted(return_value, key=lambda i: [x[0] for x in GoodsCategory.choices].index(i["key"]))

    def get_tc_activity(self, instance):
        key = instance.tc_activity
        value = instance.tc_activity_other if key == TradeControlActivity.OTHER else TradeControlActivity.get_text(key)
        return {"key": key, "value": value} if key else None

    def get_tc_product_category(self, instance):
        key = instance.tc_product_category
        return {"key": key, "value": TradeControlProductCategory.get_text(key)} if key else None


class StandardApplicationCreateSerializer(GenericApplicationCreateSerializer):
    export_type = KeyValueChoiceField(
        choices=ApplicationExportType.choices, error_messages={"required": strings.Applications.Generic.NO_EXPORT_TYPE},
    )
    have_you_been_informed = KeyValueChoiceField(
        choices=ApplicationExportLicenceOfficialType.choices, error_messages={"required": strings.Goods.INFORMED},
    )
    reference_number_on_information_form = CharField(allow_blank=True)
    goods_categories = serializers.MultipleChoiceField(
        choices=GoodsCategory.choices, required=False, allow_null=True, allow_blank=True, allow_empty=True
    )
    tc_activity = KeyValueChoiceField(
        choices=TradeControlActivity.choices,
        error_messages={"required": strings.Applications.Generic.TRADE_CONTROL_ACTIVITY_ERROR},
    )
    tc_activity_other = CharField(
        allow_blank=False, error_messages={"blank": strings.Applications.Generic.TRADE_CONTROL_ACTIVITY_OTHER_ERROR}
    )
    tc_product_category = KeyValueChoiceField(
        choices=TradeControlProductCategory.choices,
        error_messages={"required": strings.Applications.Generic.TRADE_CONTROl_PRODUCT_CATEGORY_ERROR},
    )

    class Meta:
        model = StandardApplication
        fields = GenericApplicationCreateSerializer.Meta.fields + (
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "goods_categories",
            "tc_activity",
            "tc_activity_other",
            "tc_product_category",
        )

    def __init__(self, case_type_id, **kwargs):
        super().__init__(case_type_id, **kwargs)
        self.trade_control_licence = case_type_id in [str(CaseTypeEnum.SICL.id), str(CaseTypeEnum.OICL.id)]

        if self.trade_control_licence:
            self.fields.pop("export_type")
            self.fields.pop("have_you_been_informed")
            self.fields.pop("reference_number_on_information_form")

            if not self.initial_data.get("tc_activity") == TradeControlActivity.OTHER:
                self.fields.pop("tc_activity_other")
        else:
            self.fields.pop("tc_activity")
            self.fields.pop("tc_activity_other")
            self.fields.pop("tc_product_category")

    def create(self, validated_data):
        if self.trade_control_licence:
            validated_data["export_type"] = ApplicationExportType.PERMANENT
        return super().create(validated_data)


class StandardApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    reference_number_on_information_form = CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    goods_categories = serializers.MultipleChoiceField(
        choices=GoodsCategory.choices, required=False, allow_null=True, allow_blank=True, allow_empty=True
    )

    class Meta:
        model = StandardApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + (
            "have_you_been_informed",
            "reference_number_on_information_form",
            "goods_categories",
            "is_shipped_waybill_or_lading",
            "non_waybill_or_lading_route_details",
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
        if "goods_categories" in validated_data:
            instance.goods_categories = validated_data.pop("goods_categories")

        self._update_have_you_been_informed_linked_fields(instance, validated_data)

        instance = super().update(instance, validated_data)
        return instance

    @classmethod
    def _update_have_you_been_informed_linked_fields(cls, instance, validated_data):
        instance.have_you_been_informed = validated_data.pop("have_you_been_informed", instance.have_you_been_informed)

        reference_number_on_information_form = validated_data.pop(
            "reference_number_on_information_form", instance.reference_number_on_information_form,
        )

        if instance.have_you_been_informed == YesNoChoiceType.YES:
            instance.reference_number_on_information_form = reference_number_on_information_form
        else:
            instance.reference_number_on_information_form = None

    def validate(self, data):
        validate_field(
            data,
            "is_shipped_waybill_or_lading",
            strings.Applications.Generic.RouteOfGoods.IS_SHIPPED_AIR_WAY_BILL_OR_LADING,
        )
        if data.get("is_shipped_waybill_or_lading") == False:
            validate_field(
                data,
                "non_waybill_or_lading_route_details",
                strings.Applications.Generic.RouteOfGoods.SHIPPING_DETAILS,
                required=True,
            )
        return super().validate(data)
