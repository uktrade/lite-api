from rest_framework import serializers
from cases.generated_documents.models import GeneratedCaseDocument


class GeneratedCaseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "template",
            "text",
        )
