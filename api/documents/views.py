from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView

from django.http import (
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import Http404

from api.cases.generated_documents.signing import get_certificate_data
from api.core.authentication import SharedAuthentication
from api.core.exceptions import NotFoundError
from api.documents.libraries.s3_operations import document_download_stream
from api.documents.models import Document
from api.documents.serializers import DocumentViewSerializer
from api.documents import permissions


class DocumentDetail(RetrieveAPIView):
    """
    Get information about a Document
    """

    authentication_classes = (SharedAuthentication,)
    queryset = Document.objects.all()
    permission_classes = (permissions.IsCaseworkerOrInDocumentOrganisation,)
    serializer_class = DocumentViewSerializer

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            raise NotFoundError({"document": "Document not found"})
        return super().handle_exception(exc)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return JsonResponse({"document": serializer.data})


class DownloadSigningCertificate(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        certificate = get_certificate_data()
        response = HttpResponse(content=certificate, content_type="application/x-x509-ca-cert")
        response["Content-Disposition"] = f'attachment; filename="LITECertificate.crt"'
        return response


class DocumentStream(RetrieveAPIView):
    """
    Get streamed content of a document.
    """

    authentication_classes = (SharedAuthentication,)
    queryset = Document.objects.filter(safe=True)
    permission_classes = (permissions.IsCaseworkerOrInDocumentOrganisation,)

    def retrieve(self, request, *args, **kwargs):
        document = self.get_object()
        return document_download_stream(document)
