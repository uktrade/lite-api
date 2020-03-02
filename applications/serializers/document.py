from applications.models import ApplicationDocument
from documents.serializers import DocumentSerializer


class ApplicationDocumentSerializer(DocumentSerializer):
    class Meta:
        model = ApplicationDocument
        fields = DocumentSerializer.Meta.fields + ("application",)
