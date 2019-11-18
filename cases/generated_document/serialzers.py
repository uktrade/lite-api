from rest_framework import serializers

from cases.generated_document.models import GeneratedDocument


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedDocument
        fields = (
            "id",
            "document",
            "case",
            "template",
            "name"
        )
