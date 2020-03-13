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
from lite_content.lite_api.strings import Applications as strings


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

        self._update_have_you_been_informed_linked_fields(instance, validated_data)

        self._update_reference_field(instance, "military_end_use_controls", validated_data)
        self._update_reference_field(instance, "informed_wmd", validated_data)
        self._update_reference_field(instance, "suspected_wmd", validated_data)

        self._update_eu_military_linked_fields(instance, validated_data)

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

    @classmethod
    def _update_eu_military_linked_fields(cls, instance, validated_data):
        instance.compliant_limitations_eu_ref = validated_data.pop(
            "compliant_limitations_eu_ref", instance.compliant_limitations_eu_ref
        )

        instance.is_compliant_limitations_eu = validated_data.pop(
            "is_compliant_limitations_eu", instance.is_compliant_limitations_eu
        )
        if instance.is_compliant_limitations_eu:
            instance.compliant_limitations_eu_ref = None

        instance.is_eu_military = validated_data.pop("is_eu_military", instance.is_eu_military)
        if not instance.is_eu_military:
            instance.is_compliant_limitations_eu = None
            instance.compliant_limitations_eu_ref = None

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
            validated_data, "military_end_use_controls", strings.Generic.EndUseDetails.Error.INFORMED_TO_APPLY
        )
        self._validate_linked_fields(validated_data, "informed_wmd", strings.Generic.EndUseDetails.Error.INFORMED_WMD)
        self._validate_linked_fields(validated_data, "suspected_wmd", strings.Generic.EndUseDetails.Error.SUSPECTED_WMD)
        self._validate_boolean_field(validated_data, "is_eu_military", strings.Generic.EndUseDetails.Error.EU_MILITARY)
        self._validate_eu_military_linked_fields(self.instance, validated_data)

        return validated_data

    @classmethod
    def _validate_eu_military_linked_fields(cls, instance, validated_data):
        if (
            instance.is_eu_military
            and instance.is_compliant_limitations_eu is None
            and validated_data.get("is_compliant_limitations_eu") is None
        ):
            raise serializers.ValidationError(
                {"is_compliant_limitations_eu": strings.Generic.EndUseDetails.Error.COMPLIANT_LIMITATIONS_EU}
            )

    @classmethod
    def _validate_linked_fields(cls, validated_data, linked_field, error):
        linked_boolean_field = "is_" + linked_field
        linked_boolean_field = cls._validate_boolean_field(validated_data, linked_boolean_field, error)

        if linked_boolean_field:
            linked_reference_field = linked_field + "_ref"

            if not validated_data.get(linked_reference_field):
                raise serializers.ValidationError(
                    {linked_reference_field: strings.Generic.EndUseDetails.Error.MISSING_DETAILS}
                )

    @classmethod
    def _validate_boolean_field(cls, validated_data, boolean_field, error):
        is_boolean_field_present = boolean_field in validated_data

        if is_boolean_field_present:
            boolean_field_value = validated_data[boolean_field]

            if boolean_field_value is None:
                raise serializers.ValidationError({boolean_field: error})

            return boolean_field_value
