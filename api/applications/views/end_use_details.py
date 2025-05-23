from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView

from api.applications.libraries.edit_applications import save_and_audit_end_use_details
from api.applications.libraries.get_applications import get_application
from api.applications.serializers.end_use_details import StandardEndUseDetailsUpdateSerializer
from api.core.authentication import ExporterAuthentication
from api.core.decorators import (
    authorised_to_view_application,
    application_is_major_editable,
)
from api.users.models import ExporterUser


class EndUseDetails(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    @application_is_major_editable
    def put(self, request, pk):
        application = get_application(pk)
        serializer = StandardEndUseDetailsUpdateSerializer(application, data=request.data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        save_and_audit_end_use_details(request, application, serializer)
        return JsonResponse(data=serializer.validated_data, status=status.HTTP_200_OK)
