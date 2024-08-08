from django.http import Http404
from rest_framework.generics import UpdateAPIView

from api.core.authentication import ExporterAuthentication
from api.core.permissions import IsExporterInOrganisation
from api.applications.serializers.good import GoodOnApplicationQuantityValueSerializer
from api.applications.models import BaseApplication, GoodOnApplication
from api.exporter.applications.permissions import IsApplicationEditable


class BaseExporterApplication:
    authentication_classes = (ExporterAuthentication,)
    permission_classes = (IsExporterInOrganisation,)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        try:
            self.application = BaseApplication.objects.get(pk=self.kwargs["pk"])
        except BaseApplication.DoesNotExist:
            raise Http404()

    def get_organisation(self):
        return self.application.organisation


class ApplicationQuantityValueUpdateView(BaseExporterApplication, UpdateAPIView):
    permission_classes = (
        IsExporterInOrganisation,
        IsApplicationEditable,
    )
    lookup_url_kwarg = "good_on_application_pk"
    serializer_class = GoodOnApplicationQuantityValueSerializer

    def get_queryset(self):
        return GoodOnApplication.objects.filter(application_id=self.kwargs["pk"])
