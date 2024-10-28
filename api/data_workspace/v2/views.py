from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.models import Case
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.core.helpers import str_to_bool
from api.data_workspace.v2.serializers import SIEL_TEMPLATE_ID, SIEL_REFUSAL_TEMPLATE_ID, LicenceDecisionSerializer


class DisableableLimitOffsetPagination(LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        if str_to_bool(request.GET.get("disable_pagination", False)):
            return

        return super().paginate_queryset(queryset, request, view)


class LicenceDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination

    issued_qs = Case.objects.filter(
        licences__generatedcasedocument__template_id=SIEL_TEMPLATE_ID,
        licences__generatedcasedocument__visible_to_exporter=True,
        licences__generatedcasedocument__safe=True,
    )
    refused_qs = Case.objects.filter(
        id__in=GeneratedCaseDocument.objects.filter(
            template_id=SIEL_REFUSAL_TEMPLATE_ID,
            visible_to_exporter=True,
            safe=True,
        ).values_list("case", flat=True)
    )

    queryset = (issued_qs | refused_qs).distinct().order_by("-reference_code")

    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceDecisionSerializer
