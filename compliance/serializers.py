from rest_framework import serializers

from compliance.models import OpenLicenceReturns


class OpenLicenceReturnsListSerializer(serializers.Serializer):
    pass


class OpenLicenceReturnsCreateSerializer(serializers.ModelSerializer):
    file = serializers.CharField(required=True, allow_blank=False)
    year = serializers.IntegerField(required=True)

    class Meta:
        model = OpenLicenceReturns
        fields = (
            "file",
            "year",
            "licences",
        )
