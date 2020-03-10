from rest_framework import serializers

from applications.models import OpenApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from lite_content.lite_api import strings
from static.countries.models import Country
from static.countries.serializers import CountryWithFlagsSerializer


class OpenApplicationViewSerializer(GenericApplicationViewSerializer):
    goods_types = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()

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
    military_end_use_controls_ref = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2000
    )
    informed_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)
    suspected_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)

    class Meta:
        model = OpenApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + (
            "is_military_end_use_controls",
            "military_end_use_controls_ref",
            "is_informed_wmd",
            "informed_wmd_ref",
            "is_suspected_wmd",
            "suspected_wmd_ref",
        )

    def validate(self, data):
        validated_data = super().validate(data)
        self._validate_linked_fields(validated_data, "is_military_end_use_controls", "military_end_use_controls_ref")
        self._validate_linked_fields(validated_data, "is_informed_wmd", "informed_wmd_ref")
        self._validate_linked_fields(validated_data, "is_suspected_wmd", "suspected_wmd_ref")
        return validated_data

    @classmethod
    def _validate_boolean_field(cls, validated_data, boolean_field):
        is_boolean_field_present = boolean_field in validated_data

        if is_boolean_field_present:
            boolean_field_value = validated_data[boolean_field]

            if boolean_field_value is None:
                raise serializers.ValidationError(
                    {boolean_field: strings.Applications.Generic.END_USE_DETAILS_REQUIRED}
                )

            return boolean_field_value

    @classmethod
    def _validate_linked_fields(cls, validated_data, boolean_field, reference_field):
        linked_boolean_field = cls._validate_boolean_field(validated_data, boolean_field)

        if linked_boolean_field:
            if not validated_data.get(reference_field):
                raise serializers.ValidationError(
                    {reference_field: strings.Applications.Generic.END_USE_DETAILS_REQUIRED}
                )
