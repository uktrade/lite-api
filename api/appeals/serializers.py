from rest_framework import serializers

from api.documents.libraries.process_document import process_document

from .models import Appeal, AppealDocument


class AppealDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppealDocument
        fields = (
            "id",
            "name",
            "size",
            "s3_key",
            "safe",
        )


class AppealDocumentCreateSerializer(AppealDocumentSerializer):
    def __init__(self, *args, appeal, **kwargs):
        self.appeal = appeal
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        validated_data["appeal"] = self.appeal
        document = super().create(validated_data)
        process_document(document)
        document.refresh_from_db()
        return document


class AppealSerializer(serializers.ModelSerializer):
    documents = AppealDocumentSerializer(many=True)

    class Meta:
        model = Appeal
        fields = ("id", "grounds_for_appeal", "documents")
