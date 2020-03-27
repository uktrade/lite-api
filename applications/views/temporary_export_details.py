from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView

from applications.helpers import get_temp_export_details_update_serializer
from applications.libraries.edit_applications import (
    save_and_audit_temporary_export_details,
    get_temporary_export_details_minor_edit_errors,
)
from cases.enums import CaseTypeSubTypeEnum
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users, application_in_editable_state, allowed_application_types
from lite_content.lite_api import strings
from users.models import ExporterUser


class TemporaryExportDetails(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    @allowed_application_types([CaseTypeSubTypeEnum.OPEN, CaseTypeSubTypeEnum.STANDARD])
    @application_in_editable_state()
    def put(self, request, application):
        # Prevent minor edits
        # TODO major editable decorator instead?
        if not application.is_major_editable():
            return JsonResponse(
                data={"errors": get_temporary_export_details_minor_edit_errors(request)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = get_temp_export_details_update_serializer(application.export_type)
        serializer = serializer(application, data=request.data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        save_and_audit_temporary_export_details(request, application, serializer)
        return JsonResponse(data=serializer.validated_data, status=status.HTTP_200_OK)
