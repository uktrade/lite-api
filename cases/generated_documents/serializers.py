from rest_framework import serializers

from cases.generated_documents.models import GeneratedCaseDocument
from documents.models import Document


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
