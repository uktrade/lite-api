from django.http import JsonResponse, Http404
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

import conf
from applications.models import Application
from applications.serializers import ApplicationSerializer
from conf.settings import JSON_INDENT


@permission_classes((permissions.AllowAny,))
class ApplicationList(APIView):
    """
    List all applications, or create a new application from a draft.
    """
    def get(self, request):
        snippets = Application.objects.all()
        serializer = ApplicationSerializer(snippets, many=True)
        return JsonResponse(data={'status': 'success', 'applications': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT}, safe=False)

    def post(self, request):
        serializer = ApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class ApplicationDetail(APIView):
    """
    Retrieve, update or delete a application instance.
    """
    def get_object(self, pk):
        try:
            return Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        snippet = self.get_object(pk)
        serializer = ApplicationSerializer(snippet)
        return JsonResponse(data={'status': 'success', 'application': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT})
