from rest_framework import serializers

from applications.enums import LicenceDuration
from applications.models import Licence
from lite_content.lite_api import strings


class LicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licence
        fields = (
            "application",
            "start_date",
            "duration",
            "complete",
        )

    def validate(self, data):
        """
        Check that the start is before the stop.
        """
        if data.get("duration") and (
            data["duration"] > LicenceDuration.MAX.value or data["duration"] < LicenceDuration.MIN.value
        ):
            raise serializers.ValidationError(strings.Applications.Finalise.Error.DURATION_RANGE)
        return data
