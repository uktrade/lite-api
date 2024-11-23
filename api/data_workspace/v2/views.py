import itertools

from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    F,
    Q,
)
from django.db.models.aggregates import (
    Count,
    Min,
)
from django.db.models.lookups import GreaterThan
from django.db.models.query import QuerySet

from api.applications.models import (
    GoodOnApplication,
    PartyOnApplication,
    StandardApplication,
)
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.core.helpers import str_to_bool
from api.data_workspace.v2.serializers import (
    ApplicationSerializer,
    CountrySerializer,
    DestinationSerializer,
    GoodSerializer,
    LicenceDecisionSerializer,
    LicenceDecisionType,
)
from api.staticdata.countries.models import Country
from api.staticdata.statuses.enums import CaseStatusEnum


class DisableableLimitOffsetPagination(LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        if str_to_bool(request.GET.get("disable_pagination", False)):
            return  # pragma: no cover

        return super().paginate_queryset(queryset, request, view)


class BaseViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)


class LicenceDecisionViewSet(BaseViewSet):
    serializer_class = LicenceDecisionSerializer

    class DataWorkspace:
        table_name = "licence_decisions"

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


class CountryViewSet(BaseViewSet):
    serializer_class = CountrySerializer
    queryset = Country.objects.all().order_by("id", "name")

    class DataWorkspace:
        table_name = "countries"


class DestinationViewSet(BaseViewSet):
    serializer_class = DestinationSerializer
    queryset = (
        PartyOnApplication.objects.filter(deleted_at__isnull=True)
        .exclude(application__status__status=CaseStatusEnum.DRAFT)
        .select_related("party", "party__country")
    )

    class DataWorkspace:
        table_name = "destinations"


class GoodViewSet(BaseViewSet):
    serializer_class = GoodSerializer
    queryset = GoodOnApplication.objects.exclude(application__status__status=CaseStatusEnum.DRAFT)

    class DataWorkspace:
        table_name = "goods"


class ApplicationViewSet(BaseViewSet):
    serializer_class = ApplicationSerializer
    queryset = (
        StandardApplication.objects.exclude(status__status=CaseStatusEnum.DRAFT)
        .select_related("case_type", "status")
        .annotate(
            earliest_licence_decision=Min("licence_decisions__created_at"),
            has_incorporated_goods=GreaterThan(
                Count("goods", filter=(Q(goods__is_good_incorporated=True) | Q(goods__is_onward_incorporated=True))), 0
            ),
        )
    )

    class DataWorkspace:
        table_name = "applications"

    def get_first_closed_statuses(self, queryset):
        status_map = dict(CaseStatusEnum.choices)
        closed_statuses = list(
            itertools.chain.from_iterable((status, status_map[status]) for status in CaseStatusEnum.closed_statuses())
        )
        application_ids = []
        if isinstance(queryset, list):
            application_ids = [str(s.pk) for s in queryset]
        elif isinstance(queryset, QuerySet):
            application_ids = [str(pk) for pk in queryset.values_list("pk", flat=True)]

        first_closed_status_updates = (
            Audit.objects.filter(
                target_object_id__in=application_ids,
                verb=AuditType.UPDATED_STATUS,
                payload__status__new__in=closed_statuses,
            )
            .annotate(first_closed_date=Min("created_at"))
            .values_list("target_object_id", "first_closed_date")
        )

        return dict(first_closed_status_updates)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()

        context = self.get_serializer_context()

        if args and isinstance(args[0], (QuerySet, list)) and kwargs.get("many", False):
            context["first_closed_statuses"] = self.get_first_closed_statuses(args[0])
        elif args and isinstance(args[0], StandardApplication):
            context["first_closed_statuses"] = self.get_first_closed_statuses([args[0]])
        kwargs.setdefault("context", context)

        return serializer_class(*args, **kwargs)
