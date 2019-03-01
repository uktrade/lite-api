from django.http import JsonResponse

from rest_framework import status
from applications.models import FormComplete, Application
from rest_framework.response import Response
from drafts.models import Draft
from drafts.serializers import DraftSerializer


def applications_list(request):
    if request.method == "POST":
        submit_id = request.POST.get('id', None)
        if len(Draft.objects.filter(id=submit_id)) > 0:
            draft_to_be_submitted = Draft.objects.get(id=submit_id)
            if FormComplete(draft_to_be_submitted).ready_for_submission:
                new_application = Application(id=draft_to_be_submitted.id,
                                              user_id=draft_to_be_submitted.user_id,
                                              control_code=draft_to_be_submitted.control_code,
                                              destination=draft_to_be_submitted.destination,
                                              activity=draft_to_be_submitted.activity,
                                              usage=draft_to_be_submitted.usage)
                new_application.save()

                if Application.objects.get(id=draft_to_be_submitted.id):
                    draft_to_be_submitted.delete()

                response = JsonResponse(DraftSerializer(FormComplete(draft_to_be_submitted)).data, safe=False)
                response.status_code = status.HTTP_201_CREATED
                return response
            else:
                response = JsonResponse(DraftSerializer(FormComplete(draft_to_be_submitted)).data, safe=False)
                response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                return response
        else:
            response = JsonResponse(submit_id, safe=False)
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
    else:
        response = JsonResponse({}, safe=False)
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return response
