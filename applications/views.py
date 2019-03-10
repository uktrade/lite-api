from django.http import JsonResponse

from rest_framework import status
from applications.models import Application
from applications.libraries.ValidateFormFields import ValidateFormFields
from rest_framework.response import Response
from drafts.models import Draft
from drafts.serializers import DraftSerializer
from applications.serializers import ApplicationSerializer


def applications_list(request):
    if request.method == "POST":
        submit_id = request.POST.get('id', None)

        if Draft.objects.filter(id=submit_id).exists():
            draft_to_be_submitted = Draft.objects.get(id=submit_id)

            if ValidateFormFields(draft_to_be_submitted).ready_for_submission:
                new_application = Application(id=draft_to_be_submitted.id,
                                              user_id=draft_to_be_submitted.user_id,
                                              control_code=draft_to_be_submitted.control_code,
                                              destination=draft_to_be_submitted.destination,
                                              activity=draft_to_be_submitted.activity,
                                              usage=draft_to_be_submitted.usage)
                new_application.save()

                if Application.objects.get(id=draft_to_be_submitted.id):
                    draft_to_be_submitted.delete()

                response = JsonResponse(DraftSerializer(ValidateFormFields(draft_to_be_submitted)).data, safe=False)
                response.status_code = status.HTTP_201_CREATED
                return response

            else:
                response = JsonResponse(DraftSerializer(ValidateFormFields(draft_to_be_submitted)).data, safe=False)
                response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                return response

        else:
            response = JsonResponse(submit_id, safe=False)
            response.status_code = status.HTTP_404_NOT_FOUND
            return response

    else:
        applications = Application.objects.all()
        serializer = ApplicationSerializer(applications, many=True)
        return JsonResponse(serializer.data, safe=False)
