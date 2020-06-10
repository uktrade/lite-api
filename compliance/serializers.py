from rest_framework import serializers

from compliance.models import OpenLicenceReturns


class OpenLicenceReturnsListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    year = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class OpenLicenceReturnsCreateSerializer(serializers.ModelSerializer):
    file = serializers.CharField(required=True, allow_blank=False)
    year = serializers.IntegerField(required=True)

    class Meta:
        model = OpenLicenceReturns
        fields = (
            "file",
            "year",
            "organisation",
            "licences",
        )
