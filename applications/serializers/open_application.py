from rest_framework import serializers

from applications.enums import YesNoChoiceType
from applications.models import OpenApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from conf.serializers import KeyValueChoiceField
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
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
    is_military_end_use_controls = KeyValueChoiceField(
        choices=YesNoChoiceType.yes_no_choices, allow_blank=True, allow_null=True
    )
    is_informed_wmd = KeyValueChoiceField(choices=YesNoChoiceType.yes_no_choices, allow_blank=True, allow_null=True)
    is_suspected_wmd = KeyValueChoiceField(choices=YesNoChoiceType.yes_no_choices, allow_blank=True, allow_null=True)
    is_eu_military = KeyValueChoiceField(choices=YesNoChoiceType.yes_no_na_choices, allow_blank=True, allow_null=True)

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
            "is_eu_military",
        )

    def validate(self, data):
        validated_data = super().validate(data)
        self._validate_dependent_ref_field(
            validated_data, "is_military_end_use_controls", "military_end_use_controls_ref"
        )
        self._validate_dependent_ref_field(validated_data, "is_informed_wmd", "informed_wmd_ref")
        self._validate_dependent_ref_field(validated_data, "is_suspected_wmd", "suspected_wmd_ref")
        return validated_data

    @staticmethod
    def _validate_dependent_ref_field(validated_data, yes_no_field, ref_field):
        is_yes_no_field_present = yes_no_field in validated_data

        if is_yes_no_field_present:
            yes_no_field_val = validated_data.get(yes_no_field)

            if not yes_no_field_val:
                raise serializers.ValidationError({yes_no_field: "Required!"})

            if yes_no_field_val == YesNoChoiceType.YES:
                if not validated_data.get(ref_field):
                    raise serializers.ValidationError({ref_field: "Very bad"})
