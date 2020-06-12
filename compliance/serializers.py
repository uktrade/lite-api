from rest_framework import serializers

from compliance.models import OpenLicenceReturns
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
