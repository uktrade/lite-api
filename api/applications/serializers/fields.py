from rest_framework import serializers

from api.staticdata.statuses.libraries.get_case_status import get_status_value_from_case_status_enum


class CaseStatusField(serializers.Field):
    def to_representation(self, value):
        return {
            "id": value.id,
            "key": value.status,
            "value": get_status_value_from_case_status_enum(value.status),
        }
