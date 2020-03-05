from rest_framework import serializers

from cases.generated_documents.models import GeneratedCaseDocument
from gov_users.serializers import GovUserViewSerializer


class GeneratedCaseDocumentExporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "id",
            "name",
            "created_at",
        )


class GeneratedCaseDocumentGovSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "template",
            "text",
        )


class GeneratedFinalAdviceDocumentGovSerializer(serializers.ModelSerializer):
    user = GovUserViewSerializer()

    class Meta:
        model = GeneratedCaseDocument
        fields = ("user", "created_at")
