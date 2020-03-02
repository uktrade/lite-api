from applications.models import ApplicationDocument
from documents.serializers import DocumentViewSerializer


class ApplicationDocumentViewSerializer(DocumentViewSerializer):
    class Meta:
        model = ApplicationDocument
        fields = DocumentViewSerializer.Meta.fields + ("application",)
