from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from drafts.models import Draft
from drafts.serializers import DraftSerializer


@csrf_exempt
def drafts_list(request):
    if request.method == "POST":
        control_code = request.POST.get('control_code', None)

        # Create a new draft
        new_draft = Draft(control_code=control_code)
        new_draft.save()

        # Return the new object
        draft = Draft.objects.get(id=new_draft.id)
        serializer = DraftSerializer(draft)
        return JsonResponse(serializer.data)
    else:
        drafts = Draft.objects.all()
        serializer = DraftSerializer(drafts, many=True)
        return JsonResponse(serializer.data, safe=False)


@csrf_exempt
def draft_detail(request, id):
    if request.method == "POST":
        # Pull draft info from post
        control_code = request.POST.get('control_code', None)
        activity = request.POST.get('activity', None)
        destination = request.POST.get('destination', None)
        usage = request.POST.get('usage', None)

        try:
            draft = Draft.objects.get(id=id)
        except Draft.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Update draft
        if control_code:
            draft.control_code = control_code

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

    if request.method == "DELETE":
        try:
            draft = Draft.objects.get(id=id)
        except Draft.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        draft.delete()

    if request.method == "GET":
        try:
            draft = Draft.objects.get(id=id)
        except Draft.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = DraftSerializer(draft)
        return JsonResponse(serializer.data)
