from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from api.core.authentication import ExporterAuthentication
from api.core.exceptions import NotFoundError

from api.applications.libraries.get_applications import get_application
from api.core.permissions import IsExporterInOrganisation


class ExporterApplicationMixin:
    # Mixin for views which checks the exporter is within same organisation as the application
    # Checks Exporter is authenticated

    authentication_classes = (ExporterAuthentication,)
    permission_classes = [
        IsExporterInOrganisation,
    ]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.application = get_application(self.kwargs["pk"])
        except (ObjectDoesNotExist, NotFoundError):
            raise Http404()

    def get_object(self):
        self.check_object_permissions(self.request, self.application)
        return self.application

    def get_organisation(self):
        return self.application.organisation
