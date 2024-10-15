from rest_framework import serializers

from api.licences.models import Licence


class LicenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Licence
        fields = (
            "id",
            "reference_code",
        )
