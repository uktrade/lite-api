from api.core import viewsets
from api.core.context_processors import (
    draft_status_serializer_context_processor,
    organisation_serializer_context_processor,
)

from api.applications.models import StandardApplication
from api.core.authentication import ExporterAuthentication
from api.export_licences.exporter.serializers import ExportLicenceSerializer


class ExportLicenceApplicationViewSet(viewsets.ModelViewSet):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = ExportLicenceSerializer
    serializer_context_processors = (
        draft_status_serializer_context_processor,
        organisation_serializer_context_processor,
    )
    queryset = StandardApplication.objects.all()
