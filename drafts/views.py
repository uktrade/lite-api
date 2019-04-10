from django.http import JsonResponse, Http404
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from drafts.models import Draft
from drafts.serializers import DraftBaseSerializer, DraftCreateSerializer, DraftUpdateSerializer


@permission_classes((permissions.AllowAny,))
class DraftList(APIView):
    """
    List all drafts, or create a new draft.
    """
    def get(self, request):
        drafts = Draft.objects.order_by('-created_at')
        serializer = DraftBaseSerializer(drafts, many=True)
        return JsonResponse(data={'status': 'success', 'drafts': serializer.data},
                            safe=False)

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = DraftCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'status': 'success', 'draft': serializer.data},
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
            draft = Draft.objects.get(pk=pk)
            return draft
        except Draft.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        draft = self.get_object(pk)
        serializer = DraftBaseSerializer(draft)
        return JsonResponse(data={'status': 'success', 'draft': serializer.data})

    def put(self, request, pk):
        data = JSONParser().parse(request)
        serializer = DraftUpdateSerializer(self.get_object(pk), data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'status': 'success', 'draft': serializer.data},
                                status=status.HTTP_200_OK)
        return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                            status=400)

    def delete(self, request, pk):
        draft = self.get_object(pk)
        draft.delete()
