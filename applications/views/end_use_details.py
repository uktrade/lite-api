from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView

from applications.helpers import get_application_end_use_details_update_serializer
from applications.libraries.edit_applications import save_and_audit_end_use_details
from applications.libraries.get_applications import get_application
from api.conf.authentication import ExporterAuthentication
from api.conf.decorators import authorised_to_view_application, application_in_state
from users.models import ExporterUser


class EndUseDetails(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    @application_in_state(is_major_editable=True)
    def put(self, request, pk):
        application = get_application(pk)
        serializer = get_application_end_use_details_update_serializer(application)
        serializer = serializer(application, data=request.data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        save_and_audit_end_use_details(request, application, serializer)
        return JsonResponse(data=serializer.validated_data, status=status.HTTP_200_OK)
