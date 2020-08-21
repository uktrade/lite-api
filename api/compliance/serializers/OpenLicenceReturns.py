from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


from api.compliance.models import OpenLicenceReturns
from lite_content.lite_api.strings import Compliance


class OpenLicenceReturnsListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    year = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class OpenLicenceReturnsViewSerializer(OpenLicenceReturnsListSerializer):
    returns_data = serializers.CharField()


class OpenLicenceReturnsCreateSerializer(serializers.ModelSerializer):
    returns_data = serializers.CharField(required=True, allow_blank=False)
    year = serializers.IntegerField(
        required=True, error_messages={"required": Compliance.OpenLicenceReturns.YEAR_ERROR}
    )

    class Meta:
        model = OpenLicenceReturns
        fields = (
            "id",
            "returns_data",
            "year",
            "organisation",
            "licences",
        )

    def validate_year(self, value):
        current_year = timezone.now().year
        last_year = current_year - 1

        if value not in [current_year, last_year]:
            raise ValidationError(Compliance.OpenLicenceReturns.INVALID_YEAR)

        return value
