from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from api.cases.models import Case
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import LicenceDecisionSerializer


SIEL_TEMPLATE_ID = "d159b195-9256-4a00-9bc8-1eb2cebfa1d2"


class LicenceDecisionListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = LimitOffsetPagination
    queryset = (
        Case.objects.filter(
            licences__generatedcasedocument__template_id=SIEL_TEMPLATE_ID,
            licences__generatedcasedocument__visible_to_exporter=True,
            licences__generatedcasedocument__safe=True,
        )
        .distinct()
        .order_by("-reference_code")
    )
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceDecisionSerializer
