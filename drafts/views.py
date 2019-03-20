from django.http import JsonResponse, Http404
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.settings import JSON_INDENT
from applications.models import Application
from applications.serializers import ApplicationSerializer


@permission_classes((permissions.AllowAny,))
class DraftList(APIView):
    """
    List all drafts, or create a new draft.
    """
    def get(self, request):
        drafts = Application.objects.filter(draft=True)
        serializer = ApplicationSerializer(drafts, many=True)
        return JsonResponse(data={'status': 'success', 'drafts': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT}, safe=False)

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = ApplicationSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'status': 'success', 'draft': serializer.data},
                                json_dumps_params={'indent': JSON_INDENT},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class DraftDetail(APIView):
    """
    Retrieve, update or delete a draft instance.
    """
    def get_object(self, pk):
        try:
            draft = Application.objects.get(pk=pk)
            if not draft.draft:
                raise Http404
            return draft
        except Application.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        draft = self.get_object(pk)
        serializer = ApplicationSerializer(draft)
        return JsonResponse(data={'status': 'success', 'draft': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT})

    def put(self, request, pk):
        data = JSONParser().parse(request)
        serializer = ApplicationSerializer(self.get_object(pk), data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'status': 'success', 'draft': serializer.data},
                                json_dumps_params={'indent': JSON_INDENT},
                                status=status.HTTP_201_CREATED)
        return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                            status=400)

    def delete(self, request, pk):
        draft = self.get_object(pk)
        draft.delete()
