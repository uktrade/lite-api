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
    LicenceDecisionSerializer,
    LicenceDecisionType,
)
from api.licences.enums import LicenceStatus


class DisableableLimitOffsetPagination(LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        if str_to_bool(request.GET.get("disable_pagination", False)):
            return

        return super().paginate_queryset(queryset, request, view)


class LicenceDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination

    queryset = (
        (
            Case.objects.filter(
                casedocument__generatedcasedocument__template_id__in=LicenceDecisionType.templates().values(),
                casedocument__visible_to_exporter=True,
                casedocument__safe=True,
            )
            .annotate(
                template_ids=ArrayAgg(
                    Cast("casedocument__generatedcasedocument__template_id", output_field=TextField()), distinct=True
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

    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceDecisionSerializer
