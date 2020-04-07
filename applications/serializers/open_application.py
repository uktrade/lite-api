from rest_framework import serializers

from applications.models import OpenApplication
from licences.models import Licence
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from licences.serializers import CaseLicenceViewSerializer
from applications.serializers.serializer_helper import validate_field
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from lite_content.lite_api import strings
from static.countries.models import Country
from static.countries.serializers import CountryWithFlagsSerializer


class OpenApplicationViewSerializer(GenericApplicationViewSerializer):
    goods_types = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    licence = serializers.SerializerMethodField()

    proposed_return_date = serializers.DateField(required=False)

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


class OpenApplicationCreateSerializer(GenericApplicationCreateSerializer):
    class Meta:
        model = OpenApplication
        fields = (
            "id",
            "name",
            "case_type",
            "export_type",
            "organisation",
            "status",
        )


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
