from django.http.response import Http404, JsonResponse
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from cases.models import Case, CaseNote
from cases.serializers import CaseSerializer, CaseNoteSerializer


@permission_classes((permissions.AllowAny,))
class CaseDetail(APIView):
    """
    Retrieve or update a case instance.
    """
    def get(self, request, pk):
        application = self.get_object(pk)
        serializer = CaseSerializer(application)
        return JsonResponse(data={'case': serializer.data})


@permission_classes((permissions.AllowAny,))
class CaseNoteList(APIView):
    """
    Retrieve/create case notes.
    """
    def get(self, request, pk):
        application = self.get_object(pk)
        serializer = CaseNoteSerializer(application)
        return JsonResponse(data={'case_notes': serializer.data})
