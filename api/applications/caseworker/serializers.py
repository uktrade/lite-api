from rest_framework import serializers

from api.applications.models import ApplicationDocument
from api.staticdata.statuses.enums import CaseStatusEnum


class ApplicationChangeStatusSerializer(serializers.Serializer):

    status = serializers.ChoiceField(choices=CaseStatusEnum.all())
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = (
            "id",
            "name",
            "application",
            "description",
            "document_type",
            "created_at",
            "safe",
            "description",
        )
