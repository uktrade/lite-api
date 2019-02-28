from django.http import JsonResponse

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
                new_application = Application(user_id=draft_to_be_submitted.user_id,
                                              id=draft_to_be_submitted.id,
                                              control_code=draft_to_be_submitted.control_code,
                                              destination=draft_to_be_submitted.destination,
                                              activity=draft_to_be_submitted.activity,
                                              usage=draft_to_be_submitted.usage)
                new_application.save()

                if Application.objects.get(id=draft_to_be_submitted.id):
                    draft_to_be_submitted.delete()

                response = JsonResponse(DraftSerializer(FormComplete(draft_to_be_submitted)).data, safe=False)
                response.status_code = 201
                return response
            else:
                response = JsonResponse(DraftSerializer(FormComplete(draft_to_be_submitted)).data, safe=False)
                response.status_code = 422
                return response
        else:
            response = JsonResponse(submit_id, safe=False)
            response.status_code = 404
            return response
    else:
        response = JsonResponse({}, safe=False)
        response.status_code = 405
        return response
