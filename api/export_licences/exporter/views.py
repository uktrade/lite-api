from api.core import viewsets
from api.core.context_processors import ApplicationSerializerContextProcessor

from api.applications.models import StandardApplication
from api.cases.enums import CaseTypeEnum
from api.core.authentication import ExporterAuthentication
from api.export_licences.exporter.serializers import ExportLicenceSerializer


class ExportLicenceApplicationViewSet(viewsets.ModelViewSet):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = ExportLicenceSerializer
    serializer_context_processors = (ApplicationSerializerContextProcessor(CaseTypeEnum.SIEL.id),)
    queryset = StandardApplication.objects.all()
