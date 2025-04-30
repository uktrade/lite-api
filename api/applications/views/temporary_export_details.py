from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.exceptions import ValidationError

from api.applications.serializers.temporary_export_details import TemporaryExportDetailsUpdateSerializer
from api.applications.libraries.edit_applications import save_and_audit_temporary_export_details
from api.applications.libraries.get_applications import get_application
from api.cases.enums import CaseTypeReferenceEnum
from api.applications.enums import ApplicationExportType
from api.core.authentication import ExporterAuthentication
from api.core.decorators import (
    authorised_to_view_application,
    allowed_application_types,
    application_is_major_editable,
)
from api.users.models import ExporterUser


class TemporaryExportDetails(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    @allowed_application_types([CaseTypeReferenceEnum.EXPORT_LICENCE, CaseTypeReferenceEnum.SIEL])
    @application_is_major_editable
    def put(self, request, pk):
        application = get_application(pk)
        if application.export_type == ApplicationExportType.PERMANENT:
            raise ValidationError(
                {"temp_export_details": ["Cannot update temporary export details for a permanent export type"]}
            )

        serializer = TemporaryExportDetailsUpdateSerializer(application, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            save_and_audit_temporary_export_details(request, application, serializer)
            return JsonResponse(data=serializer.validated_data, status=status.HTTP_200_OK)
