from rest_framework import serializers
from rest_framework.fields import CharField

from applications.enums import GoodsCategory, YesNoChoiceType
from applications.mixins.serializers import PartiesSerializerMixin
from applications.models import StandardApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from applications.serializers.good import GoodOnApplicationViewSerializer
from lite_content.lite_api import strings


class StandardApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    goods_categories = serializers.SerializerMethodField()

    def get_goods_categories(self, instance):
        # Return a formatted key, value format of GoodsCategories
        # Order according to the choices in GoodsCategory
        return_value = [{"key": x, "value": GoodsCategory.get_text(x)} for x in instance.goods_categories or []]
        return sorted(return_value, key=lambda i: [x[0] for x in GoodsCategory.choices].index(i["key"]))

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
            )
        )


class StandardApplicationCreateSerializer(GenericApplicationCreateSerializer):
    goods_categories = serializers.MultipleChoiceField(
        choices=GoodsCategory.choices, required=False, allow_null=True, allow_blank=True, allow_empty=True
    )

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "name",
            "case_type",
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "goods_categories",
            "organisation",
            "status",
        )


class StandardApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    reference_number_on_information_form = CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    goods_categories = serializers.MultipleChoiceField(
        choices=GoodsCategory.choices, required=False, allow_null=True, allow_blank=True, allow_empty=True
    )
    military_end_use_controls_ref = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=225
    )
    informed_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=225)
    suspected_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)
    compliant_limitations_eu_ref = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2000
    )

    class Meta:
        model = StandardApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + (
            "have_you_been_informed",
            "reference_number_on_information_form",
            "goods_categories",
            "is_military_end_use_controls",
            "military_end_use_controls_ref",
            "is_informed_wmd",
            "informed_wmd_ref",
            "is_suspected_wmd",
            "suspected_wmd_ref",
            "is_eu_military",
            "is_compliant_limitations_eu",
            "compliant_limitations_eu_ref",
        )

    def update(self, instance, validated_data):
        if "goods_categories" in validated_data:
            instance.goods_categories = validated_data.pop("goods_categories")

        instance.have_you_been_informed = validated_data.pop("have_you_been_informed", instance.have_you_been_informed)

        reference_number_on_information_form = validated_data.pop(
            "reference_number_on_information_form", instance.reference_number_on_information_form,
        )

        if instance.have_you_been_informed == YesNoChoiceType.YES:
            instance.reference_number_on_information_form = reference_number_on_information_form
        else:
            instance.reference_number_on_information_form = None

        instance = super().update(instance, validated_data)
        return instance

    def validate(self, data):
        validated_data = super().validate(data)
        self._validate_linked_fields(
            validated_data, "military_end_use_controls", strings.Applications.EndUseDetailsErrors.INFORMED_TO_APPLY
        )
        self._validate_linked_fields(
            validated_data, "informed_wmd", strings.Applications.EndUseDetailsErrors.INFORMED_WMD
        )
        self._validate_linked_fields(
            validated_data, "suspected_wmd", strings.Applications.EndUseDetailsErrors.SUSPECTED_WMD
        )
        self._validate_boolean_field(
            validated_data, "is_eu_military", strings.Applications.EndUseDetailsErrors.EU_MILITARY
        )

        self._validate_boolean_field(
            validated_data,
            "is_compliant_limitations_eu",
            strings.Applications.EndUseDetailsErrors.IS_COMPLIANT_LIMITATIONS_EU,
        )

        return validated_data

    @classmethod
    def _validate_linked_fields(cls, validated_data, linked_field, error):
        linked_boolean_field = "is_" + linked_field
        linked_boolean_field = cls._validate_boolean_field(validated_data, linked_boolean_field, error)

        if linked_boolean_field:
            linked_reference_field = linked_field + "_ref"

            if not validated_data.get(linked_reference_field):
                raise serializers.ValidationError(
                    {linked_reference_field: strings.Applications.EndUseDetailsErrors.MISSING_REFERENCE}
                )

    @classmethod
    def _validate_boolean_field(cls, validated_data, boolean_field, error):
        is_boolean_field_present = boolean_field in validated_data

        if is_boolean_field_present:
            boolean_field_value = validated_data[boolean_field]

            if boolean_field_value is None:
                raise serializers.ValidationError({boolean_field: error})

            return boolean_field_value
