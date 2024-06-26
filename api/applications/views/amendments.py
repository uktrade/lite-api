from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, JsonResponse
from rest_framework.generics import CreateAPIView
from rest_framework import serializers
from rest_framework import status

from api.core.authentication import ExporterAuthentication
from api.core.exceptions import NotFoundError
from api.core.permissions import IsExporterInOrganisation
from api.applications.libraries.get_applications import get_application


class AmendmentSerializer(serializers.Serializer):
    pass


class CreateApplicationAmendment(CreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    permission_classes = [
        IsExporterInOrganisation,
    ]
    serializer_class = AmendmentSerializer

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.amendment_application = None

        try:
            self.application = get_application(pk=self.kwargs["pk"])
        except (ObjectDoesNotExist, NotFoundError):
            raise Http404()
        # TODO: More validation to prevent creating amendment of something we should not

    def get_organisation(self):
        return self.application.organisation

    def perform_create(self, serializer):
        self.amendment_application = self.application.create_amendment(self.request.user)

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return JsonResponse(
            {
                "id": str(self.amendment_application.id),
            },
            status=status.HTTP_201_CREATED,
        )
