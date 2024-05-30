from django.db import transaction
from django.http import JsonResponse
from rest_framework import generics
from rest_framework import status

from api.applications.models import StandardApplication
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.core.authentication import ExporterAuthentication


class CreateApplicationCopyView(generics.CreateAPIView):
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    def post(self, request, case_pk):
        try:
            application = StandardApplication.objects.get(id=case_pk)
        except StandardApplication.DoesNotExist:
            return JsonResponse(
                data={"errors": {"application": "Invalid Standard application"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        copied_application = application.clone()

        return JsonResponse(data={"id": copied_application.id}, status=status.HTTP_201_CREATED)
