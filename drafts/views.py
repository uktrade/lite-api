from django.http import JsonResponse, Http404
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from conf.settings import JSON_INDENT
from drafts.models import Draft
from drafts.serializers import DraftSerializer


@permission_classes((permissions.AllowAny,))
class DraftList(APIView):
    """
    List all drafts, or create a new draft.
    """
    def get(self, request):
        drafts = Draft.objects.all()
        serializer = DraftSerializer(drafts, many=True)
        return JsonResponse(data={'status': 'success', 'drafts': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT}, safe=False)

    def post(self, request):
        control_code = request.POST.get('control_code', None)
        user_id = request.POST.get('user_id', None)

        if not user_id:
            return JsonResponse({}, status=422)

        # Create a new draft
        new_draft = Draft(control_code=control_code,
                          user_id=user_id)
        new_draft.save()

        # Return the new object
        draft = Draft.objects.get(id=new_draft.id)
        serializer = DraftSerializer(draft)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)


@permission_classes((permissions.AllowAny,))
class DraftDetail(APIView):
    """
    Retrieve, update or delete a draft instance.
    """
    def get_object(self, pk):
        try:
            return Draft.objects.get(pk=pk)
        except Draft.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        draft = self.get_object(pk)
        serializer = DraftSerializer(draft)
        return JsonResponse(data={'status': 'success', 'draft': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT})

    def post(self, request, pk):
        # Pull draft info from post
        name = request.POST.get('name', None)
        control_code = request.POST.get('control_code', None)
        activity = request.POST.get('activity', None)
        destination = request.POST.get('destination', None)
        usage = request.POST.get('usage', None)

        draft = self.get_object(pk)

        # Update draft
        if name.strip() is '':
            return JsonResponse({
                "status": "error",
                "errors":
                    {
                        "name": "Invalid Application Name"
                    }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            draft.name = name

        if control_code:
            return JsonResponse({
                "status": "error",
                "errors":
                    {
                        "control_code": "Invalid Control Code"
                    }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            # draft.control_code = control_code

        if activity:
            draft.activity = activity

        if destination:
            draft.destination = destination

        if usage:
            draft.usage = usage

        draft.save()

        # Return the updated object
        serializer = DraftSerializer(draft)
        return JsonResponse(serializer.data)

    def delete(self, request, pk):
        draft = self.get_object(pk)
        draft.delete()
