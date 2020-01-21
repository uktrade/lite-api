from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from cases.libraries.get_case import get_case
from cases.models import CaseDocument
from conf.authentication import GovAuthentication, ExporterAuthentication
from conf.exceptions import NotFoundError
from documents.libraries.s3_operations import download_document_from_s3
from documents.models import Document
from documents.serializers import DocumentViewSerializer


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


class DocumentDownload(APIView):
    authentication_classes = (ExporterAuthentication, GovAuthentication,)

    """
    Download a document
    """
    def get(self, request, pk):
        try:
            document = Document.objects.get(id=pk)
            return download_document_from_s3(s3_key=document.s3_key, original_file_name=document.name)
        except Document.DoesNotExist:
            raise NotFoundError({"document": "Document not found"})


class ExporterCaseDocumentDownload(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, case_pk, file_pk):
        case = get_case(case_pk)
        if case.organisation != request.user.organisation:
            return HttpResponse(status.HTTP_401_UNAUTHORIZED)
        try:
            document = CaseDocument.objects.get(id=file_pk, case=case)
            return JsonResponse({"document": document.id})
        except Document.DoesNotExist:
            raise NotFoundError({"document": "Document not found"})
