from django.http import JsonResponse
from rest_framework import generics
from rest_framework import status

from api.applications.models import StandardApplication
from api.core.authentication import ExporterAuthentication


class CreateApplicationCopyView(generics.CreateAPIView):
    authentication_classes = (ExporterAuthentication,)

    def post(self, request, pk):
        try:
            application = StandardApplication.objects.get(id=pk)
        except StandardApplication.DoesNotExist:
            return JsonResponse(
                data={"errors": {"application": "Invalid Standard application"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return JsonResponse(data={}, status=status.HTTP_201_CREATED)
