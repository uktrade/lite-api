from api.core.authentication import GovAuthentication
from api.core.permissions import CanCaseworkersManageOrgainsation
from api.organisations.models import Organisation
from django.http import Http404

from api.organisations.caseworker.serializers.serializers import ExporterUserCreateSerializer

from rest_framework.generics import CreateAPIView


class CreateExporterUser(CreateAPIView):
    authentication_classes = (GovAuthentication,)

    serializer_class = ExporterUserCreateSerializer
    permission_classes = [CanCaseworkersManageOrgainsation]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        try:
            self.organisation = Organisation.objects.get(pk=self.kwargs["org_pk"])
        except Organisation.DoesNotExist:
            raise Http404()

    def perform_create(self, serializer):
        super().perform_create(serializer)
        sites = [site.id for site in serializer.validated_data["sites"]]
        email = serializer.validated_data["email"]

        self.organisation.notify_exporter_user_added(email)
        self.organisation.add_case_note_add_export_user(self.request.user, sites, email)

    def get_serializer(self, data):
        data["organisation"] = self.organisation.id
        return self.serializer_class(data=data)
