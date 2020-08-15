from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView

from api.cases.generated_documents.signing import get_certificate_data
from api.conf.authentication import GovAuthentication, SharedAuthentication
from api.conf.exceptions import NotFoundError
from api.documents.models import Document
from api.documents.serializers import DocumentViewSerializer


class DocumentDetail(APIView):
    """
    Get information about a Document
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Returns document metadata
        """
        try:
            document = Document.objects.get(id=pk)
            serializer = DocumentViewSerializer(document)
            return JsonResponse({"document": serializer.data})
        except Document.DoesNotExist:
            raise NotFoundError({"document": "Document not found"})


class DownloadSigningCertificate(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        certificate = get_certificate_data()
        response = HttpResponse(content=certificate, content_type="application/x-x509-ca-cert")
        response["Content-Disposition"] = f'attachment; filename="LITECertificate.crt"'
        return response
