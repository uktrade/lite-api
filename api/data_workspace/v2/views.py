import functools
import operator

from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    Case as DBCase,
    F,
    Q,
    TextField,
    Value,
    When,
)
from django.db.models.functions import Cast

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.core.helpers import str_to_bool
from api.data_workspace.v2.serializers import (
    LicenceDecisionDerivedSerializer,
    LicenceDecisionSerializer,
    LicenceDecisionType,
)
from api.licences.enums import LicenceStatus


class DisableableLimitOffsetPagination(LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        if str_to_bool(request.GET.get("disable_pagination", False)):
            return

        return super().paginate_queryset(queryset, request, view)


class LicenceDecisionDerivedViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceDecisionDerivedSerializer

    def get_queryset(self):
        queryset = (
            (
                Case.objects.filter(
                    casedocument__generatedcasedocument__template_id__in=LicenceDecisionType.templates().values(),
                    casedocument__visible_to_exporter=True,
                    casedocument__safe=True,
                )
                .annotate(
                    template_ids=ArrayAgg(
                        Cast("casedocument__generatedcasedocument__template_id", output_field=TextField()),
                        distinct=True,
                    )
                )
                .filter(
                    functools.reduce(
                        operator.or_,
                        [Q(template_ids=[template_id]) for template_id in LicenceDecisionType.templates().values()],
                    )
                )
                .annotate(
                    decision=DBCase(
                        *[
                            When(template_ids=[template_id], then=Value(decision.value))
                            for decision, template_id in LicenceDecisionType.templates().items()
                        ]
                    )
                )
                .distinct()
            )
            .union(
                Case.objects.filter(
                    pk__in=list(
                        Audit.objects.filter(
                            payload__status=LicenceStatus.REVOKED,
                            verb=AuditType.LICENCE_UPDATED_STATUS,
                        ).values_list("target_object_id", flat=True)
                    )
                ).annotate(
                    template_ids=Value([], output_field=ArrayField(TextField())),
                    decision=Value("revoked", output_field=TextField()),
                ),
                all=True,
            )
            .order_by("-reference_code")
        )
        return queryset


class LicenceDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceDecisionSerializer

    def get_queryset(self):
        queryset = (
            (
                Case.objects.filter(
                    licence_decisions__decision__in=[LicenceDecisionType.ISSUED, LicenceDecisionType.REFUSED],
                )
                .annotate(
                    unique_decisions=ArrayAgg("licence_decisions__decision", distinct=True),
                )
                .filter(unique_decisions__len=1)
                .annotate(decision=F("unique_decisions__0"))
            )
            .union(
                Case.objects.filter(
                    licence_decisions__decision__in=[LicenceDecisionType.REVOKED],
                )
                .annotate(
                    unique_decisions=ArrayAgg("licence_decisions__decision", distinct=True),
                )
                .filter(unique_decisions__len=1)
                .annotate(decision=F("unique_decisions__0")),
                all=True,
            )
            .order_by("-reference_code")
        )
        return queryset
