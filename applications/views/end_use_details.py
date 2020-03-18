from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView

from applications.helpers import get_application_end_use_details_update_serializer
from applications.libraries.edit_applications import (
    get_end_use_details_minor_edit_errors,
    save_and_audit_end_use_details,
)
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users, application_in_editable_state
from users.models import ExporterUser


class EndUseDetails(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    @application_in_editable_state()
    def put(self, request, application):
        # Prevent minor edits of the end use details
        if not application.is_major_editable():
            return JsonResponse(
                data={"errors": get_end_use_details_minor_edit_errors(request)}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = get_application_end_use_details_update_serializer(application)
        serializer = serializer(application, data=request.data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        save_and_audit_end_use_details(request, application, serializer)
        return JsonResponse(data=serializer.validated_data, status=status.HTTP_200_OK)
