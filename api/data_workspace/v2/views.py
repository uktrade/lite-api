from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from api.cases.models import Case
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import CaseLicenceSerializer

SIEL_TEMPLATE_ID = "d159b195-9256-4a00-9bc8-1eb2cebfa1d2"


class LicencesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = LimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = CaseLicenceSerializer

    def get_queryset(self):
        licence_documents = GeneratedCaseDocument.objects.filter(
            template_id=SIEL_TEMPLATE_ID, visible_to_exporter=True, safe=True
        )
        return (
            Case.objects.filter(
                licences__generatedcasedocument__in=licence_documents,
            )
            .distinct()
            .order_by("-reference_code")
        )
