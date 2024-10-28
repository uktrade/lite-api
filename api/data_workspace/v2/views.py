from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    Case as DBCase,
    Q,
    TextField,
    Value,
    When,
)
from django.db.models.functions import Cast

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

    queryset = (
        Case.objects.filter(
            casedocument__generatedcasedocument__template_id__in=[SIEL_TEMPLATE_ID, SIEL_REFUSAL_TEMPLATE_ID],
            casedocument__visible_to_exporter=True,
            casedocument__safe=True,
        )
        .annotate(
            template_ids=ArrayAgg(
                Cast("casedocument__generatedcasedocument__template_id", output_field=TextField()), distinct=True
            )
        )
        .filter(Q(template_ids=[SIEL_TEMPLATE_ID]) | Q(template_ids=[SIEL_REFUSAL_TEMPLATE_ID]))
        .annotate(
            decision=DBCase(
                When(template_ids=[SIEL_TEMPLATE_ID], then=Value("issued")),
                When(template_ids=[SIEL_REFUSAL_TEMPLATE_ID], then=Value("refused")),
            )
        )
        .distinct()
        .order_by("-reference_code")
    )

    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceDecisionSerializer
