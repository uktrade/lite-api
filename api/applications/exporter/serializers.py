from rest_framework import serializers

from api.staticdata.statuses.enums import CaseStatusEnum


class ApplicationChangeStatusSerializer(serializers.Serializer):

    status = serializers.ChoiceField(choices=CaseStatusEnum.all())
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)