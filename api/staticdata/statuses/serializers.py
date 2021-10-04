from rest_framework import serializers

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


class CaseStatusSerializer(serializers.ModelSerializer):
    key = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    def get_key(self, instance):
        return instance.status

    def get_value(self, instance):
        return CaseStatusEnum.get_text(instance.status)

    class Meta:
        model = CaseStatus
        fields = (
            "id",
            "key",
            "value",
            "status",
            "priority",
        )
