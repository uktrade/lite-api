from rest_framework import serializers

from api.applications.enums import LicenceDuration
from api.licences.models import Licence
from lite_content.lite_api import strings


class LicenceCreateSerializer(serializers.ModelSerializer):
    reference_code = serializers.CharField(max_length=30, allow_blank=False, allow_null=False)

    class Meta:
        model = Licence
        fields = ("case", "reference_code", "start_date", "duration", "status")

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
