from rest_framework import serializers

from cases.enums import CaseDocumentState
from conf.serializers import KeyValueChoiceField
from documents.libraries.process_document import process_document
from documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    s3_key = serializers.SerializerMethodField()
    type = KeyValueChoiceField(choices=CaseDocumentState.choices)

    class Meta:
        model = Document
        fields = ("name", "s3_key", "size", "created_at", "description", "type", "safe")

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else "File not ready"

    def create(self, validated_data):
        document = super(DocumentSerializer, self).create(validated_data)
        document.save()
        process_document(document)
        return document
