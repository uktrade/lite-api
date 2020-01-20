from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import GovAuthentication, ExporterAuthentication
from conf.exceptions import NotFoundError
from documents.models import Document
from documents.serializers import DocumentViewSerializer
from documents.helpers import download_document
from goods.libraries.get_goods import get_good


class DocumentDetail(APIView):
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


class ExporterGoodDocumentDownload(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, good_pk, file_pk):
        good = get_good(good_pk)
        if good.organisation != request.user.organisation:
            return HttpResponse(status.HTTP_401_UNAUTHORIZED)
        return download_document(file_pk)
