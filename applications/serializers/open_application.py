from rest_framework import serializers
from rest_framework.fields import CharField

from applications.enums import ApplicationExportType
from applications.models import OpenApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from applications.serializers.serializer_helper import validate_field
from cases.enums import CaseTypeEnum
from conf.serializers import KeyValueChoiceField
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from licences.models import Licence
from licences.serializers import CaseLicenceViewSerializer
from lite_content.lite_api import strings
from static.countries.models import Country
from static.countries.serializers import CountryWithFlagsSerializer
from static.trade_control.enums import TradeControlProductCategory, TradeControlActivity


class OpenApplicationViewSerializer(GenericApplicationViewSerializer):
    goods_types = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    licence = serializers.SerializerMethodField()
    proposed_return_date = serializers.DateField(required=False)
    tc_activity = serializers.SerializerMethodField()
    tc_product_category = serializers.SerializerMethodField()

    class Meta:
        model = OpenApplication
        fields = GenericApplicationViewSerializer.Meta.fields + (
            "activity",
            "usage",
            "goods_types",
            "destinations",
            "additional_documents",
            "is_military_end_use_controls",
            "military_end_use_controls_ref",
            "is_informed_wmd",
            "informed_wmd_ref",
            "is_suspected_wmd",
            "suspected_wmd_ref",
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

    def get_goods_types(self, application):
        goods_types = GoodsType.objects.filter(application=application)
        return FullGoodsTypeSerializer(goods_types, many=True).data

    def get_destinations(self, application):
        countries = Country.objects.filter(countries_on_application__application=application)
        serializer = CountryWithFlagsSerializer(countries, many=True, context={"active_flags_only": True})
        return {"type": "countries", "data": serializer.data}

    def get_licence(self, instance):
        licence = Licence.objects.filter(application=instance).first()
        return CaseLicenceViewSerializer(licence).data

    def get_tc_activity(self, instance):
        key = instance.tc_activity
        value = instance.tc_activity_other if key == TradeControlActivity.OTHER else TradeControlActivity.get_text(key)
        return {"key": key, "value": value} if key else None

    def get_tc_product_category(self, instance):
        key = instance.tc_product_category
        return {"key": key, "value": TradeControlProductCategory.get_text(key)} if key else None


class OpenApplicationCreateSerializer(GenericApplicationCreateSerializer):
    export_type = KeyValueChoiceField(
        choices=ApplicationExportType.choices, error_messages={"required": strings.Applications.Generic.NO_EXPORT_TYPE},
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
        model = OpenApplication
        fields = GenericApplicationCreateSerializer.Meta.fields + (
            "export_type",
            "tc_activity",
            "tc_activity_other",
            "tc_product_category",
        )

    def __init__(self, case_type_id, **kwargs):
        super().__init__(case_type_id, **kwargs)
        self.trade_control_licence = case_type_id in [str(CaseTypeEnum.SICL.id), str(CaseTypeEnum.OICL.id)]

        if self.trade_control_licence:
            self.fields.pop("export_type")

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


class OpenApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    class Meta:
        model = OpenApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + (
            "is_shipped_waybill_or_lading",
            "non_waybill_or_lading_route_details",
        )

    def __init__(self, *args, **kwargs):
        super(OpenApplicationUpdateSerializer, self).__init__(*args, **kwargs)

        if self.get_initial().get("is_shipped_waybill_or_lading") == "True":
            if hasattr(self, "initial_data"):
                self.initial_data["non_waybill_or_lading_route_details"] = None

    def validate(self, data):
        validate_field(
            data,
            "is_shipped_waybill_or_lading",
            strings.Applications.Generic.RouteOfGoods.IS_SHIPPED_AIR_WAY_BILL_OR_LADING,
        )
        if data.get("is_shipped_waybill_or_lading") == False:
            validate_field(
                data, "non_waybill_or_lading_route_details", strings.Applications.Generic.RouteOfGoods.SHIPPING_DETAILS
            )
        return super().validate(data)
