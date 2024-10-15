from rest_framework import serializers

from api.licences.models import Licence


class LicenceStatusSerializer(serializers.Serializer):
    name = serializers.CharField(source="*")


class SIELLicenceSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Licence
        fields = (
            "id",
            "reference_code",
        )
