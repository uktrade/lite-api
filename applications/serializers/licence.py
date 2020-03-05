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
            "licence_duration",
            "finalised",
        )

    def validate(self, data):
        """
        Check that the start is before the stop.
        """
        if data.get("licence_duration") and (
            data["licence_duration"] > LicenceDuration.MAX.value or data["licence_duration"] < LicenceDuration.MIN.value
        ):
            raise serializers.ValidationError(strings.Applications.Finalise.Error.DURATION_RANGE)
        return data
