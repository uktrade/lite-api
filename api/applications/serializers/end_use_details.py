from rest_framework import serializers

from api.applications.models import BaseApplication
from api.applications.serializers.serializer_helper import validate_field
from lite_content.lite_api.strings import Applications as strings


class F680EndUseDetailsUpdateSerializer(serializers.ModelSerializer):
    intended_end_use = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2200)

    class Meta:
        model = BaseApplication
        fields = ("intended_end_use",)

    def validate(self, data):
        validate_field(data, "intended_end_use", strings.Generic.EndUseDetails.Error.INTENDED_END_USE)
        return super().validate(data)


class StandardEndUseDetailsUpdateSerializer(serializers.ModelSerializer):
    military_end_use_controls_ref = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=225
    )
    informed_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=225)
    suspected_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2200)
    intended_end_use = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2200)
    compliant_limitations_eu_ref = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2200
    )

    class Meta:
        model = BaseApplication
        fields = (
            "is_military_end_use_controls",
            "military_end_use_controls_ref",
            "is_informed_wmd",
            "informed_wmd_ref",
            "is_suspected_wmd",
            "suspected_wmd_ref",
            "intended_end_use",
            "is_eu_military",
            "is_compliant_limitations_eu",
            "compliant_limitations_eu_ref",
        )

    def validate(self, data):
        _validate_linked_fields(
            data, "military_end_use_controls", strings.Generic.EndUseDetails.Error.INFORMED_TO_APPLY
        )
        _validate_linked_fields(data, "informed_wmd", strings.Generic.EndUseDetails.Error.INFORMED_WMD)
        _validate_linked_fields(data, "suspected_wmd", strings.Generic.EndUseDetails.Error.SUSPECTED_WMD)
        validate_field(data, "intended_end_use", strings.Generic.EndUseDetails.Error.INTENDED_END_USE)
        validate_field(data, "is_eu_military", strings.Generic.EndUseDetails.Error.EU_MILITARY)
        _validate_eu_military_linked_fields(self.instance, data)

        return super().validate(data)

    def update(self, instance, validated_data):
        _update_reference_field(instance, "military_end_use_controls", validated_data)
        _update_reference_field(instance, "informed_wmd", validated_data)
        _update_reference_field(instance, "suspected_wmd", validated_data)
        _update_eu_military_linked_fields(instance, validated_data)

        return super().update(instance, validated_data)


class OpenEndUseDetailsUpdateSerializer(serializers.ModelSerializer):
    military_end_use_controls_ref = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=225
    )
    informed_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=225)
    suspected_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2200)
    intended_end_use = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2200)

    class Meta:
        model = BaseApplication
        fields = (
            "is_military_end_use_controls",
            "military_end_use_controls_ref",
            "is_informed_wmd",
            "informed_wmd_ref",
            "is_suspected_wmd",
            "suspected_wmd_ref",
            "intended_end_use",
        )

    def validate(self, data):
        _validate_linked_fields(
            data, "military_end_use_controls", strings.Generic.EndUseDetails.Error.INFORMED_TO_APPLY
        )
        _validate_linked_fields(data, "informed_wmd", strings.Generic.EndUseDetails.Error.INFORMED_WMD)
        _validate_linked_fields(data, "suspected_wmd", strings.Generic.EndUseDetails.Error.SUSPECTED_WMD)
        validate_field(data, "intended_end_use", strings.Generic.EndUseDetails.Error.INTENDED_END_USE)

        return super().validate(data)

    def update(self, instance, validated_data):
        _update_reference_field(instance, "military_end_use_controls", validated_data)
        _update_reference_field(instance, "informed_wmd", validated_data)
        _update_reference_field(instance, "suspected_wmd", validated_data)

        return super().update(instance, validated_data)


def _validate_linked_fields(data, linked_field, error):
    linked_boolean_field_name = "is_" + linked_field
    linked_boolean_field = validate_field(data, linked_boolean_field_name, error)

    if linked_boolean_field:
        linked_reference_field_name = linked_field + "_ref"

        validate_field(
            data,
            linked_reference_field_name,
            strings.Generic.EndUseDetails.Error.MISSING_DETAILS,
            required=True,
        )


def _validate_eu_military_linked_fields(instance, data):
    if (
        instance.is_eu_military
        and instance.is_compliant_limitations_eu is None
        and data.get("is_compliant_limitations_eu") is None
    ):
        raise serializers.ValidationError(
            {"is_compliant_limitations_eu": strings.Generic.EndUseDetails.Error.COMPLIANT_LIMITATIONS_EU}
        )


def _update_reference_field(instance, linked_field, validated_data):
    linked_reference_field = linked_field + "_ref"
    updated_reference_field = validated_data.pop(linked_reference_field, getattr(instance, linked_reference_field))
    setattr(instance, linked_reference_field, updated_reference_field)

    linked_boolean_field = "is_" + linked_field
    updated_boolean_field = validated_data.pop(linked_boolean_field, getattr(instance, linked_boolean_field))
    setattr(instance, linked_boolean_field, updated_boolean_field)

    if not updated_boolean_field:
        setattr(instance, linked_reference_field, None)


def _update_eu_military_linked_fields(instance, validated_data):
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
