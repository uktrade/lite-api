from api.core.authentication import GovAuthentication
from api.core.permissions import CanCaseworkersManageOrgainsation
from api.organisations.models import Organisation

from api.organisations.caseworker.serializers.serializers import ExporterUserCreateSerializer

from rest_framework.generics import CreateAPIView
from django.http import Http404


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
        self.orgainsation.notify_exporter_user_added(serializer.validated_data["email"])
        self.orgainsation.add_case_note_add_export_user(
            self.request.user, serializer.data["sites"], serializer.validated_data["email"]
        )
