from rest_framework import serializers

from cases.enums import CaseDocumentState
from conf.serializers import KeyValueChoiceField
from documents.libraries.process_document import process_document
from documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    type = KeyValueChoiceField(choices=CaseDocumentState.choices)

    class Meta:
        model = Document
        fields = ("name", "s3_key", "size", "created_at", "description", "type", "safe")

    def create(self, validated_data):
        document = super(DocumentSerializer, self).create(validated_data)
        document.save()
        process_document(document)
        return document
