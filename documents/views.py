from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.parsers import FileUploadParser
from rest_framework.views import APIView

from cases.libraries.get_case import get_case
from cases.models import CaseDocument
from conf.authentication import GovAuthentication, ExporterAuthentication
from conf.exceptions import NotFoundError
from documents.libraries.s3_operations import document_download_stream, get_file_from_request
from documents.models import Document, TestDocument
from documents.serializers import DocumentViewSerializer
from lite_content.lite_api.strings import Documents


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


class UploadTest(APIView):
    parser_classes = (FileUploadParser,)

    def post(self, request):
        found, file = get_file_from_request(request)
        doc = TestDocument.objects.create(
            name=file.name,
            file=file
        )
        return JsonResponse({"document": "abc"}, status=status.HTTP_201_CREATED)


class ExporterCaseDocumentDownload(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, case_pk, file_pk):
        case = get_case(case_pk)
        if case.organisation != request.user.organisation:
            return HttpResponse(status.HTTP_401_UNAUTHORIZED)
        try:
            document = CaseDocument.objects.get(id=file_pk, case=case)
            return document_download_stream(document)
        except Document.DoesNotExist:
            raise NotFoundError({"document": Documents.DOCUMENT_NOT_FOUND})
