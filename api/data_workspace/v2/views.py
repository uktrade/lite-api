import itertools

from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from django.db.models import (
    F,
    Prefetch,
    Q,
)
from django.db.models.aggregates import (
    Count,
    Min,
)
from django.db.models.lookups import GreaterThan

from api.applications.models import (
    GoodOnApplication,
    PartyOnApplication,
    StandardApplication,
)
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import LicenceDecision
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.core.helpers import str_to_bool
from api.data_workspace.v2.serializers import (
    ApplicationSerializer,
    CountrySerializer,
    DestinationSerializer,
    GoodDescriptionSerializer,
    GoodSerializer,
    LicenceDecisionSerializer,
    UnitSerializer,
)
from api.staticdata.countries.models import Country
from api.staticdata.report_summaries.models import ReportSummary
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.units.enums import Units


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
    queryset = (
        LicenceDecision.objects.filter(previous_decision__isnull=True)
        .exclude(excluded_from_statistics_reason__isnull=False)
        .prefetch_related("case__licence_decisions", "case__licence_decisions__licence")
        .select_related("case")
        .order_by("-case__reference_code")
    )

    class DataWorkspace:
        table_name = "licence_decisions"


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


class GoodDescriptionViewSet(BaseViewSet):
    serializer_class = GoodDescriptionSerializer
    queryset = (
        ReportSummary.objects.select_related("prefix", "subject")
        .prefetch_related("goods_on_application")
        .exclude(goods_on_application__isnull=True)
        .annotate(good_id=F("goods_on_application__id"))
        .order_by("good_id", "prefix", "subject")
    )

    class DataWorkspace:
        table_name = "goods_descriptions"


def get_closed_statuses():
    status_map = dict(CaseStatusEnum.choices)
    return list(
        itertools.chain.from_iterable((status, status_map[status]) for status in CaseStatusEnum.closed_statuses())
    )


class ApplicationViewSet(BaseViewSet):
    serializer_class = ApplicationSerializer
    queryset = (
        StandardApplication.objects.exclude(status__status=CaseStatusEnum.DRAFT)
        .select_related("case_type", "status")
        .prefetch_related(
            Prefetch(
                "baseapplication_ptr__case_ptr__audit_trail",
                queryset=Audit.objects.filter(
                    payload__status__new__in=get_closed_statuses(), verb=AuditType.UPDATED_STATUS
                ).order_by("created_at"),
                to_attr="closed_status_updates",
            )
        )
        .annotate(
            first_licence_decision_created_at=Min("licence_decisions__created_at"),
            has_incorporated_goods=GreaterThan(
                Count("goods", filter=(Q(goods__is_good_incorporated=True) | Q(goods__is_onward_incorporated=True))), 0
            ),
        )
    )

    class DataWorkspace:
        table_name = "applications"



class UnitViewSet(viewsets.ViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)

    def list(self, request):
        units = [{"code": code, "description": description} for code, description in Units.choices]
        return Response(UnitSerializer(units, many=True).data)

    def retrieve(self, request, pk):
        units = dict(Units.choices)
        description = units[pk]
        return Response(UnitSerializer({"code": pk, "description": description}).data)

    class DataWorkspace:
        table_name = "units"
