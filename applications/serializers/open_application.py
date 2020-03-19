from rest_framework import serializers

from applications.models import OpenApplication, Licence
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from applications.serializers.licence import LicenceSerializer
from conf.serializers import PrimaryKeyRelatedSerializerField
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from static.countries.models import Country
from static.countries.serializers import CountryWithFlagsSerializer


class OpenApplicationViewSerializer(GenericApplicationViewSerializer):
    goods_types = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    licence = PrimaryKeyRelatedSerializerField(queryset=Licence.objects.all(), serializer=LicenceSerializer)

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
        )

    def get_goods_types(self, application):
        goods_types = GoodsType.objects.filter(application=application)
        return FullGoodsTypeSerializer(goods_types, many=True).data

    def get_destinations(self, application):
        countries = Country.objects.filter(countries_on_application__application=application)
        serializer = CountryWithFlagsSerializer(countries, many=True)
        return {"type": "countries", "data": serializer.data}


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
        fields = GenericApplicationUpdateSerializer.Meta.fields
