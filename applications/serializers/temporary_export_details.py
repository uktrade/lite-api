from django.utils import timezone
from rest_framework import serializers

from applications.models import BaseApplication
from applications.serializers.end_use_details import _validate_field


class TemporaryExportDetailsUpdateSerializer(serializers.ModelSerializer):
    temp_export_details = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2200)
    is_temp_direct_control = serializers.BooleanField(
        required=False, error_messages={"invalid": "Answer the question about direct controls with Yes or No"}
    )
    temp_direct_control_details = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2200
    )
    proposed_return_date = serializers.DateField(
        required=False,
        error_messages={
            "invalid": "Enter the proposed date the products will return to the UK and include a day, a month, and a year",
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
        _validate_field(data, "temp_export_details", "Enter the temporary export details")
        is_temp_direct_control_value = _validate_field(
            data, "is_temp_direct_control", "Answer the question about direct controls with Yes or No"
        )

        # Only validate temp_direct_control_details if its parent is_temp_direct_control is False
        if is_temp_direct_control_value is False:
            if not data.get("temp_direct_control_details"):
                raise serializers.ValidationError({"temp_direct_control_details": "Enter details for direct control"})

        # Validate temp_direct_control_details if its parent is_temp_direct_control is False and exists on the instance
        if (
            self.instance.is_temp_direct_control is False
            and not self.instance.temp_direct_control_details
            and not data.get("temp_direct_control_details")
        ):
            raise serializers.ValidationError({"temp_direct_control_details": "Enter details for direct control"})

        today = timezone.now().date()
        if "proposed_return_date" in data:
            if data["proposed_return_date"] < today:
                raise serializers.ValidationError({"proposed_return_date": "The proposed date must be in the future"})

        return super().validate(data)

    def update(self, instance, validated_data):
        # skip temp_export_details
        # skip proposed_return_date
        instance.temp_direct_control_details = validated_data.pop(
            "temp_direct_control_details", instance.temp_direct_control_details
        )

        instance.is_temp_direct_control = validated_data.pop("is_temp_direct_control", instance.is_temp_direct_control)
        # if true then details should be none
        if instance.is_temp_direct_control:
            instance.temp_direct_control_details = None

        # TODO proposed_return_date
        return super().update(instance, validated_data)
