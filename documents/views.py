from django.http import JsonResponse
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from documents.models import Document
from documents.serializers import DocumentViewSerializer


class DocumentDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Returns a list of documents on the specified good
        """
        print(pk)
        print(Document.objects.all())
        document = Document.objects.get(id=pk)
        serializer = DocumentViewSerializer(document)
        return JsonResponse({'document': serializer.data})