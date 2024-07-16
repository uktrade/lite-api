from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, JsonResponse
from rest_framework.generics import CreateAPIView
from rest_framework import serializers
from rest_framework import status

from api.applications.libraries.get_applications import get_application
from api.core.authentication import ExporterAuthentication
from api.core.decorators import application_can_invoke_major_edit
from api.core.exceptions import NotFoundError, BadRequestError
from api.core.permissions import IsExporterInOrganisation
from api.licences.models import Licence


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

    def get_organisation(self):
        return self.application.organisation

    def perform_create(self, serializer):
        # Create a clone of the application in question and set the original application
        # to a superseded status.  Amendment applications are new copies of the original
        # which can be edited by exporters as if they were a completely new draft.
        # Caseworker commentary is not copied to the amendment application but persists
        # on the old superseded application
        self.amendment_application = self.application.create_amendment(self.request.user)

    @application_can_invoke_major_edit
    def create(self, request, *args, **kwargs):
        # At this stage we aren't totally sure how we should deal with applications
        # that have licences being amended.  So raise a meaningful error when this is attempted.
        application_has_licence = Licence.objects.filter_non_draft_licences(application=self.application).count() > 0
        if application_has_licence:
            raise BadRequestError({"non_field_errors": "Application has at least one licence so cannot be amended."})

        super().create(request, *args, **kwargs)
        return JsonResponse(
            {
                "id": str(self.amendment_application.id),
            },
            status=status.HTTP_201_CREATED,
        )
