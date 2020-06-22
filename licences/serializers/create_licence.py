from rest_framework import serializers
from common.serializers import EnumField

from applications.enums import LicenceDuration
from licences.enums import LicenceStatus
from licences.models import Licence
from lite_content.lite_api import strings


class LicenceSerializer(serializers.ModelSerializer):
    status = EnumField(LicenceStatus, required=False)

    class Meta:
        model = Licence
        fields = (
            "application",
            "start_date",
            "duration",
            "status"
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
