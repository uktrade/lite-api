from rest_framework import serializers

from documents.models import Document


class GeneratedCaseDocumentViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = (
            "id",
            "name",
            "created_at",
        )
