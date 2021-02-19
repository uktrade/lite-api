from rest_framework import serializers

from api.applications.models import ApplicationDocument
from api.documents.libraries.process_document import process_document
from api.applications.serializers.good import DocumentOnOrganisationSerializer


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    document_on_organisation = DocumentOnOrganisationSerializer(required=False, write_only=True)

    class Meta:
        model = ApplicationDocument
        fields = "__all__"

    def create(self, validated_data):
        document = super().create(validated_data)
        document.save()
        process_document(document)
        return document
