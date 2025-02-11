from rest_framework import viewsets

from api.cases.enums import CaseTypeEnum
from api.core.authentication import ExporterAuthentication
from api.organisations.libraries.get_organisation import get_request_user_organisation
from api.organisations.filters import CurrentExporterUserOrganisationFilter
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status

from api.f680.models import F680Application
from api.f680.exporter.serializers import F680ApplicationSerializer


class F680ApplicationViewSet(viewsets.ModelViewSet):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = F680ApplicationSerializer
    queryset = F680Application.objects.all()
    lookup_url_kwarg = "f680_application_id"
    filter_backends = [CurrentExporterUserOrganisationFilter]

    def get_serializer_context(self):
        serializer_context = super().get_serializer_context()
        serializer_context["organisation"] = get_request_user_organisation(self.request)
        serializer_context["default_status"] = get_case_status_by_status(CaseStatusEnum.DRAFT)
        serializer_context["case_type_id"] = CaseTypeEnum.F680.id
        return serializer_context
