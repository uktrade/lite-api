from rest_framework import serializers

from conf.serializers import KeyValueChoiceField
from static.f680_clearance_types.enums import F680ClearanceTypeEnum
from static.f680_clearance_types.models import F680ClearanceType


class F680ClearanceTypeSerializer(serializers.ModelSerializer):
    type = KeyValueChoiceField(choices=F680ClearanceTypeEnum.choices)

    class Meta:
        model = F680ClearanceType
        fields = (
            "id",
            "type",
        )
