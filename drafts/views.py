import reversion
from django.http import JsonResponse, Http404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from drafts.models import Draft
from drafts.serializers import DraftBaseSerializer, DraftCreateSerializer, DraftUpdateSerializer


class DraftList(APIView):
    permission_classes = (AllowAny,)
    """
    List all drafts, or create a new draft.
    """
    def get(self, request):
        drafts = Draft.objects.order_by('-created_at')
        serializer = DraftBaseSerializer(drafts, many=True)
        return JsonResponse(data={'status': 'success', 'drafts': serializer.data},
                            safe=False)

    def post(self, request):
        serializer = DraftCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'status': 'success', 'draft': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class DraftDetail(APIView):
    permission_classes = (AllowAny,)
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
        with reversion.create_revision():
            serializer = DraftUpdateSerializer(self.get_object(pk), data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                # Store some version meta-information.
                # reversion.set_user(request.user)              # No user information yet
                reversion.set_comment("Created Draft Revision")
                return JsonResponse(data={'status': 'success', 'draft': serializer.data},
                                    status=status.HTTP_200_OK)
            return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                                status=400)

    def delete(self, request, pk):
        draft = self.get_object(pk)
        draft.delete()
