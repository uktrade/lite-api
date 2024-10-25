from rest_framework import serializers

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import (
    CaseStatus,
    CaseSubStatus,
)


class CaseStatusSerializer(serializers.ModelSerializer):
    key = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    is_terminal = serializers.SerializerMethodField()
    is_read_only = serializers.SerializerMethodField()

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
            "is_terminal",
            "is_read_only",
            "is_major_editable",
            "can_invoke_major_editable",
            "is_caseworker_operable",
        )

    def get_is_terminal(self, instance) -> bool:
        return instance.is_terminal

    def get_is_read_only(self, instance) -> bool:
        return instance.is_read_only


class CaseStatusPropertiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStatus
        fields = (
            "is_terminal",
            "is_read_only",
            "is_major_editable",
            "can_invoke_major_editable",
        )


class CaseSubStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseSubStatus
        fields = (
            "id",
            "name",
        )
