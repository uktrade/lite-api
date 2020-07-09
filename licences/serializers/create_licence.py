from rest_framework import serializers

from applications.enums import LicenceDuration
from licences.models import Licence
from lite_content.lite_api import strings


class LicenceCreateSerializer(serializers.ModelSerializer):
    reference_code = serializers.CharField(max_length=30, required=True)

    class Meta:
        model = Licence
        fields = (
            "application",
            "reference_code",
            "start_date",
            "duration",
            "is_complete",
        )

    def validate(self, data):
        """
        Check that the duration is valid
        """
        validated_data = super().validate(data)
        if (
            validated_data["duration"] > LicenceDuration.MAX.value
            or validated_data["duration"] < LicenceDuration.MIN.value
        ):
            raise serializers.ValidationError(strings.Applications.Finalise.Error.DURATION_RANGE)
        return data
