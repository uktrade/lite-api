from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView

from api.applications.helpers import get_temp_export_details_update_serializer
from api.applications.libraries.edit_applications import save_and_audit_temporary_export_details
from api.applications.libraries.get_applications import get_application
from api.cases.enums import CaseTypeSubTypeEnum
from api.core.authentication import ExporterAuthentication
from api.core.decorators import (
    authorised_to_view_application,
    allowed_application_types,
    application_in_state,
)
from api.users.models import ExporterUser


class TemporaryExportDetails(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    @allowed_application_types([CaseTypeSubTypeEnum.OPEN, CaseTypeSubTypeEnum.STANDARD])
    @application_in_state(is_major_editable=True)
    def put(self, request, pk):
        application = get_application(pk)
        serializer = get_temp_export_details_update_serializer(application.export_type)
        serializer = serializer(application, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            save_and_audit_temporary_export_details(request, application, serializer)
            return JsonResponse(data=serializer.validated_data, status=status.HTTP_200_OK)
