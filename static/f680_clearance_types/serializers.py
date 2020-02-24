from rest_framework import serializers

from static.f680_clearance_types.models import F680ClearanceType


class F680ClearanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = F680ClearanceType
        fields = (
            "id",
            "name",
        )
