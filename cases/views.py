from django.http.response import Http404, JsonResponse
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from cases.models import Case
from cases.serializers import CaseSerializer


@permission_classes((permissions.AllowAny,))
class CaseDetail(APIView):
    """
    Retrieve or update a case instance.
    """
    def get_object(self, pk):
        try:
            return Case.objects.get(pk=pk)
        except Case.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        application = self.get_object(pk)
        serializer = CaseSerializer(application)
        return JsonResponse(data={'status': 'success', 'case': serializer.data})
