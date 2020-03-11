from rest_framework import serializers

from applications.models import OpenApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from lite_content.lite_api.strings import Applications as strings
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
        required=False, allow_blank=True, allow_null=True, max_length=225
    )
    informed_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=225)
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

    def update(self, instance, validated_data):
        self._update_reference_field(instance, "military_end_use_controls", validated_data)
        self._update_reference_field(instance, "informed_wmd", validated_data)
        self._update_reference_field(instance, "suspected_wmd", validated_data)

        instance = super().update(instance, validated_data)
        return instance

    @classmethod
    def _update_reference_field(cls, instance, linked_field, validated_data):
        linked_reference_field = linked_field + "_ref"
        updated_reference_field = validated_data.pop(linked_reference_field, getattr(instance, linked_reference_field))
        setattr(instance, linked_reference_field, updated_reference_field)

        linked_boolean_field = "is_" + linked_field
        updated_boolean_field = validated_data.pop(linked_boolean_field, getattr(instance, linked_boolean_field))
        setattr(instance, linked_boolean_field, updated_boolean_field)

        if not updated_boolean_field:
            setattr(instance, linked_reference_field, None)

    def validate(self, data):
        validated_data = super().validate(data)
        self._validate_linked_fields(
            validated_data, "military_end_use_controls", strings.EndUseDetailsErrors.INFORMED_TO_APPLY
        )
        self._validate_linked_fields(validated_data, "informed_wmd", strings.EndUseDetailsErrors.INFORMED_WMD)
        self._validate_linked_fields(validated_data, "suspected_wmd", strings.EndUseDetailsErrors.SUSPECTED_WMD)
        return validated_data

    @classmethod
    def _validate_linked_fields(cls, validated_data, linked_field, error):
        linked_boolean_field = "is_" + linked_field
        linked_boolean_field = cls._validate_boolean_field(validated_data, linked_boolean_field, error)

        if linked_boolean_field:
            linked_reference_field = linked_field + "_ref"

            if not validated_data.get(linked_reference_field):
                raise serializers.ValidationError(
                    {linked_reference_field: strings.EndUseDetailsErrors.MISSING_REFERENCE}
                )

    @classmethod
    def _validate_boolean_field(cls, validated_data, boolean_field, error):
        is_boolean_field_present = boolean_field in validated_data

        if is_boolean_field_present:
            boolean_field_value = validated_data[boolean_field]

            if boolean_field_value is None:
                raise serializers.ValidationError({boolean_field: error})

            return boolean_field_value
