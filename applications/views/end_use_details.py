from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView

from applications.libraries.edit_applications import edit_end_use_details, save_and_audit_end_use_details
from applications.serializers.end_use_details import EndUseDetailsUpdateSerializer
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users, application_in_editable_state
from users.models import ExporterUser


class EndUseDetails(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    @application_in_editable_state()
    def put(self, request, application):
        # Prevent minor edits of the end use details
        end_use_details_error = edit_end_use_details(application, request)
        if end_use_details_error:
            return end_use_details_error

        serializer = EndUseDetailsUpdateSerializer(
            application, data=request.data, application_type=application.case_type.sub_type, partial=True
        )

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        save_and_audit_end_use_details(request, application, serializer)
        return JsonResponse(data=serializer.validated_data, status=status.HTTP_200_OK)