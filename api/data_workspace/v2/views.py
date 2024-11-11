from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F

from api.applications.models import (
    GoodOnApplication,
    PartyOnApplication,
    StandardApplication,
)
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
            return

        return super().paginate_queryset(queryset, request, view)


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


class ApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = ApplicationSerializer
    queryset = StandardApplication.objects.exclude(status__status=CaseStatusEnum.terminal_statuses())


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = CountrySerializer
    queryset = Country.objects.all().order_by("id", "name")


class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = DestinationSerializer
    queryset = PartyOnApplication.objects.exclude(deleted_at__isnull=True)


class GoodViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = GoodSerializer
    queryset = GoodOnApplication.objects.all()
