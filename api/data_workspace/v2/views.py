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
from api.cases.models import (
    Advice,
    Case,
)
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.core.helpers import str_to_bool
from api.data_workspace.v2.serializers import (
    ApplicationSerializer,
    CountrySerializer,
    DestinationSerializer,
    GoodDescriptionSerializer,
    GoodOnLicenceSerializer,
    GoodSerializer,
    GoodRatingSerializer,
    LicenceDecisionSerializer,
    LicenceDecisionType,
    LicenceRefusalCriteriaSerializer,
)
from api.licences.enums import LicenceStatus
from api.licences.models import GoodOnLicence
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.models import Country
from api.staticdata.report_summaries.models import ReportSummary
from api.staticdata.statuses.enums import CaseStatusEnum


class DisableableLimitOffsetPagination(LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        if str_to_bool(request.GET.get("disable_pagination", False)):
            return  # pragma: no cover

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
    queryset = (
        StandardApplication.objects.exclude(status__status=CaseStatusEnum.DRAFT)
        .select_related("case_type")
        .prefetch_related("goods")
    )


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
    queryset = (
        PartyOnApplication.objects.filter(deleted_at__isnull=True)
        .exclude(application__status__status=CaseStatusEnum.DRAFT)
        .select_related("party", "party__country")
    )


class GoodViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = GoodSerializer
    queryset = GoodOnApplication.objects.exclude(application__status__status=CaseStatusEnum.DRAFT)


class GoodRatingViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = GoodRatingSerializer
    queryset = ControlListEntry.objects.annotate(good_id=F("goodonapplication__id")).exclude(good_id__isnull=True)


class GoodDescriptionViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = GoodDescriptionSerializer
    queryset = (
        ReportSummary.objects.select_related("prefix", "subject")
        .prefetch_related("goods_on_application")
        .exclude(goods_on_application__isnull=True)
        .annotate(good_id=F("goods_on_application__id"))
    )


class GoodOnLicenceViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = GoodOnLicenceSerializer
    queryset = GoodOnLicence.objects.exclude(
        licence__case__status__status=CaseStatusEnum.DRAFT,
        licence__status=LicenceStatus.DRAFT,
    )


class LicenceRefusalCriteriaViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceRefusalCriteriaSerializer
    queryset = (
        Advice.objects.filter(
            case__licence_decisions__decision="refused",
            team_id="58e77e47-42c8-499f-a58d-94f94541f8c6",  # Just care about LU advice
        )
        .only("denial_reasons__display_value", "case__licence_decisions__id")
        .exclude(denial_reasons__display_value__isnull=True)  # This removes refusals without any criteria
        .values_list("denial_reasons__display_value", "case__licence_decisions__id")
        .order_by()  # We need to remove the order_by to make sure the distinct works
        .distinct()
    )
