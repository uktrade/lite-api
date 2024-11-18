from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer


from api.applications.models import PartyOnApplication
from api.cases.models import LicenceDecision
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.core.helpers import str_to_bool
from api.data_workspace.v2.serializers import (
    CountrySerializer,
    DestinationSerializer,
    LicenceDecisionSerializer,
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


class LicenceDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceDecisionSerializer
    queryset = (
        LicenceDecision.objects.filter(parent__isnull=True)
        .exclude(excluded_from_statistics_reason__isnull=False)
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
