from rest_framework import serializers

from applications.models import BaseApplication
from applications.serializers.end_use_details import _validate_field


class TemporaryExportDetailsUpdateSerializer(serializers.ModelSerializer):
    temp_export_details = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2200)
    # is_temp_direct_control = models.BooleanField(blank=True, default=None, null=True)
    temp_direct_control_details = serializers.CharField(required=False, allow_blank=True, allow_null=True,
                                                        max_length=2200)
    proposed_return_date = serializers.DateField(required=False)

    class Meta:
        model = BaseApplication
        fields = ("temp_export_details",
                  "is_temp_direct_control",
                  "temp_direct_control_details",
                  "proposed_return_date",)

    def validate(self, data):
        _validate_field(data, "temp_export_details", "Enter the temporary export details")
        temp_dir_control = _validate_field(data, "is_temp_direct_control",
                                           "Answer the question about direct controls with Yes or No")
        if temp_dir_control:
            _validate_field(data, "temp_direct_control_details", "Enter details", required=True)
        # TODO proposed_return_date
        return super().validate(data)

    def update(self, instance, validated_data):
        # skip temp_export_details
        # skip proposed_return_date
        instance.temp_direct_control_details = validated_data.pop(
            "temp_direct_control_details", instance.temp_direct_control_details
        )

        instance.is_temp_direct_control = validated_data.pop(
            "is_temp_direct_control", instance.is_temp_direct_control
        )
        # if true then details should be none
        if instance.is_temp_direct_control:
            instance.temp_direct_control_details = None

        # TODO proposed_return_date
        return super().update(instance, validated_data)
