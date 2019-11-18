from django.http import JsonResponse
from rest_framework.views import APIView

from cases.generated_document.models import GeneratedDocument
from cases.generated_document.serialzers import GeneratedDocumentSerializer
from cases.libraries.get_case import get_case


class GeneratedDocuments(APIView):
    def get(self, request, pk):
        case = get_case(pk)
        generated_docs = GeneratedDocument.objects.filter(case=case)
        serializer = GeneratedDocumentSerializer(generated_docs, many=True)
        return JsonResponse({"documents": serializer.data})
