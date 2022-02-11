from django.utils import timezone
from rest_framework import serializers

from api.applications.models import BaseApplication
from api.applications.serializers.serializer_helper import validate_field
from lite_content.lite_api.strings import Applications as strings


class TemporaryExportDetailsUpdateSerializer(serializers.ModelSerializer):
    temp_export_details = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2200)
    is_temp_direct_control = serializers.BooleanField(
        required=False,
        error_messages={"invalid": strings.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL},
    )
    temp_direct_control_details = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2200
    )
    proposed_return_date = serializers.DateField(
        error_messages={
            "invalid": strings.Generic.TemporaryExportDetails.Error.PROPOSED_RETURN_DATE_INVALID,
        },
    )

    class Meta:
        model = BaseApplication
        fields = (
            "temp_export_details",
            "is_temp_direct_control",
            "temp_direct_control_details",
            "proposed_return_date",
        )

    def validate(self, data):
        validate_field(
            data, "temp_export_details", strings.Generic.TemporaryExportDetails.Error.TEMPORARY_EXPORT_DETAILS
        )
        is_temp_direct_control_value = validate_field(
            data, "is_temp_direct_control", strings.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL, required=True
        )

        # Only validate temp_direct_control_details if its parent is_temp_direct_control is False
        if is_temp_direct_control_value is False:
            if not data.get("temp_direct_control_details"):
                raise serializers.ValidationError(
                    {
                        "temp_direct_control_details": strings.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL_MISSING_DETAILS
                    }
                )

        # Validate temp_direct_control_details if its parent is_temp_direct_control is False and exists on the instance
        if (
            self.instance.is_temp_direct_control is False
            and not self.instance.temp_direct_control_details
            and not data.get("temp_direct_control_details")
        ):
            raise serializers.ValidationError(
                {
                    "temp_direct_control_details": strings.Generic.TemporaryExportDetails.Error.PRODUCTS_UNDER_DIRECT_CONTROL_MISSING_DETAILS
                }
            )

        validated_data = super().validate(data)

        today = timezone.now().date()
        if "proposed_return_date" in validated_data:
            if validated_data.get("proposed_return_date"):
                if validated_data["proposed_return_date"] <= today:
                    raise serializers.ValidationError(
                        {
                            "proposed_return_date": strings.Generic.TemporaryExportDetails.Error.PROPOSED_DATE_NOT_IN_FUTURE
                        }
                    )
                validated_data["proposed_return_date"] = str(validated_data["proposed_return_date"])
            else:
                raise serializers.ValidationError(
                    {"proposed_return_date": strings.Generic.TemporaryExportDetails.Error.PROPOSED_RETURN_DATE_BLANK}
                )

        return validated_data

    def update(self, instance, validated_data):
        instance.temp_export_details = validated_data.pop("temp_export_details", instance.temp_export_details)
        instance.proposed_return_date = validated_data.pop("proposed_return_date", instance.proposed_return_date)
        instance.temp_direct_control_details = validated_data.pop(
            "temp_direct_control_details", instance.temp_direct_control_details
        )
        instance.is_temp_direct_control = validated_data.pop("is_temp_direct_control", instance.is_temp_direct_control)
        # if true then dependent details field should be set to none
        if instance.is_temp_direct_control:
            instance.temp_direct_control_details = None

        return super().update(instance, validated_data)
