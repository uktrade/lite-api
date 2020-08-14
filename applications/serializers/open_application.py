from rest_framework import serializers
from rest_framework.fields import CharField

from applications.enums import ApplicationExportType, GoodsTypeCategory, ContractType
from applications.libraries.goodstype_category_helpers import (
    set_goods_and_countries_for_open_media_application,
    set_goods_and_countries_for_open_crypto_application,
    set_goods_and_countries_for_open_dealer_application,
    set_destinations_for_uk_continental_shelf_application,
)
from applications.mixins.serializers import PartiesSerializerMixin
from applications.models import OpenApplication
from applications.serializers.advice import CountryWithFlagsSerializer
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from applications.serializers.serializer_helper import validate_field
from cases.enums import CaseTypeEnum
from api.conf.serializers import KeyValueChoiceField
from api.goodstype.serializers import GoodsTypeViewSerializer
from licences.models import Licence
from licences.serializers.view_licence import CaseLicenceViewSerializer
from lite_content.lite_api import strings
from static.countries.models import Country
from static.countries.serializers import CountrySerializer
from static.trade_control.enums import TradeControlProductCategory, TradeControlActivity


class OpenApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods_types = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    licence = serializers.SerializerMethodField()
    proposed_return_date = serializers.DateField(required=False)
    trade_control_activity = serializers.SerializerMethodField()
    trade_control_product_categories = serializers.SerializerMethodField()
    goodstype_category = serializers.SerializerMethodField()

    class Meta:
        model = OpenApplication
        fields = (
            GenericApplicationViewSerializer.Meta.fields
            + PartiesSerializerMixin.Meta.fields
            + (
                "activity",
                "usage",
                "goods_types",
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
                "trade_control_activity",
                "trade_control_product_categories",
                "goodstype_category",
                "contains_firearm_goods",
            )
        )

    def get_goods_types(self, application):
        goods_types = application.goods_type.all().prefetch_related("countries", "countries__flags")
        default_countries = list(Country.objects.filter(countries_on_application__application_id=application.id))
        return GoodsTypeViewSerializer(goods_types, default_countries=default_countries, many=True).data

    def get_goodstype_category(self, instance):
        key = instance.goodstype_category
        value = GoodsTypeCategory.get_text(key)
        return {"key": key, "value": value}

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


class OpenApplicationCreateSerializer(GenericApplicationCreateSerializer):
    goodstype_category = KeyValueChoiceField(
        choices=GoodsTypeCategory.choices,
        error_messages={"required": strings.Applications.Generic.OIEL_GOODSTYPE_CATEGORY_ERROR},
    )
    export_type = KeyValueChoiceField(
        choices=ApplicationExportType.choices, error_messages={"required": strings.Applications.Generic.NO_EXPORT_TYPE},
    )
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
    contains_firearm_goods = serializers.BooleanField(required=False)

    class Meta:
        model = OpenApplication
        fields = GenericApplicationCreateSerializer.Meta.fields + (
            "export_type",
            "trade_control_activity",
            "trade_control_activity_other",
            "trade_control_product_categories",
            "goodstype_category",
            "contains_firearm_goods",
        )

    def __init__(self, case_type_id, **kwargs):
        super().__init__(case_type_id, **kwargs)
        self.trade_control_licence = case_type_id in [str(CaseTypeEnum.SICL.id), str(CaseTypeEnum.OICL.id)]

        # Remove fields from serializer depending on the application being for a Trade Control Licence
        if self.trade_control_licence:
            self.fields.pop("export_type")
            self.fields.pop("goodstype_category")

            if not self.initial_data.get("trade_control_activity") == TradeControlActivity.OTHER:
                self.fields.pop("trade_control_activity_other")
        else:
            self.fields.pop("trade_control_activity")
            self.fields.pop("trade_control_activity_other")
            self.fields.pop("trade_control_product_categories")

        if case_type_id == str(CaseTypeEnum.HMRC.id):
            self.fields.pop("goodstype_category")

        self.crypto_application = (
            True if self.initial_data.get("goodstype_category") == GoodsTypeCategory.CRYPTOGRAPHIC else False
        )
        self.media_application = (
            True if self.initial_data.get("goodstype_category") == GoodsTypeCategory.MEDIA else False
        )
        if self.media_application or self.crypto_application:
            self.fields.pop("export_type")

    def validate(self, data):
        if data.get("goodstype_category") in [GoodsTypeCategory.MILITARY, GoodsTypeCategory.UK_CONTINENTAL_SHELF]:
            if "contains_firearm_goods" not in data:
                raise serializers.ValidationError(
                    {"contains_firearm_goods": strings.Applications.Generic.NO_ANSWER_FIREARMS}
                )
        return data

    def create(self, validated_data):
        # Trade Control Licences are always permanent
        if self.trade_control_licence or self.crypto_application:
            validated_data["export_type"] = ApplicationExportType.PERMANENT
        elif self.media_application:
            validated_data["export_type"] = ApplicationExportType.TEMPORARY

        application = super().create(validated_data)

        if self.media_application:
            set_goods_and_countries_for_open_media_application(application)
        elif self.crypto_application:
            set_goods_and_countries_for_open_crypto_application(application)
        elif validated_data.get("goodstype_category") == GoodsTypeCategory.DEALER:
            set_goods_and_countries_for_open_dealer_application(application)
        elif validated_data.get("goodstype_category") == GoodsTypeCategory.UK_CONTINENTAL_SHELF:
            set_destinations_for_uk_continental_shelf_application(application)

        return application


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


class ContractTypeDataSerializer(serializers.Serializer):
    contract_types = serializers.MultipleChoiceField(
        choices=ContractType.choices,
        allow_empty=False,
        error_messages={"empty": strings.ContractTypes.NO_CONTRACT_TYPES},
    )
    other_contract_type_text = serializers.CharField(
        max_length=150,
        required=True,
        allow_blank=False,
        error_messages={"blank": strings.ContractTypes.OTHER_TEXT_BLANK},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.get_initial().get("contract_types"):
            self.initial_data["contract_types"] = []
        if ContractType.OTHER_CONTRACT_TYPE not in self.get_initial().get("contract_types"):
            self.fields.pop("other_contract_type_text")


class CountryOnApplicationViewSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    country = serializers.SerializerMethodField(read_only=True)
    flags = serializers.SerializerMethodField(read_only=True)
    contract_types = serializers.SerializerMethodField(read_only=True)
    other_contract_type_text = serializers.CharField(read_only=True, allow_null=True)

    def get_country(self, instance):
        if self.context.get("active_flags_only"):
            return CountryWithFlagsSerializer(
                instance.country, context={"with_active_flags": True}, read_only=True
            ).data
        else:
            return CountrySerializer(instance.country, read_only=True).data

    def get_flags(self, instance):
        return list(instance.flags.values("id", "name"))

    def get_contract_types(self, instance):
        return instance.contract_types
