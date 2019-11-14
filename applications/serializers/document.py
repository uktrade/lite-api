from rest_framework import serializers

from applications.models import ApplicationDocument
from documents.libraries.process_document import process_document


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = '__all__'

    def create(self, validated_data):
        document = super(ApplicationDocumentSerializer, self).create(validated_data)
        document.save()
        process_document(document)
        return document
