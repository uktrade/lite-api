from django.db import transaction
from django.http import JsonResponse
from rest_framework import generics
from rest_framework import status

from api.applications.models import StandardApplication
from api.core.authentication import ExporterAuthentication


class CreateApplicationCloneView(generics.CreateAPIView):
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

        data = request.data
        cloned_application = application.clone(data.get("entities", []))

        return JsonResponse(data={"id": cloned_application.id}, status=status.HTTP_201_CREATED)
