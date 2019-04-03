from django.http.response import Http404, JsonResponse
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser

from cases.models import Case
from cases.serializers import CaseSerializer
from applications.serializers import ApplicationUpdateSerializer


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

    def put(self, request, pk):
        data = JSONParser().parse(request)
        serializer = ApplicationUpdateSerializer(self.get_object(pk), data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'status': 'success', 'draft': serializer.data},
                                status=status.HTTP_200_OK)
        return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                            status=400)
