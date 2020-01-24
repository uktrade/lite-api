from django.http import JsonResponse
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.exceptions import NotFoundError
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
