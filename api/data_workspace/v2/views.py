import itertools

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
from rest_framework import viewsets
from rest_framework.pagination import (
    CursorPagination,
    LimitOffsetPagination,
)
from rest_framework.settings import api_settings
from rest_framework_csv.renderers import PaginatedCSVRenderer

from api.applications.models import (
    GoodOnApplication,
    PartyOnApplication,
    StandardApplication,
)
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import (
    Advice,
    LicenceDecision,
)
from api.conf.pagination import CreatedAtCursorPagination
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import (
    ApplicationSerializer,
    CountrySerializer,
    DestinationSerializer,
    FootnoteSerializer,
    GoodDescriptionSerializer,
    GoodOnLicenceSerializer,
    GoodRatingSerializer,
    GoodSerializer,
    LicenceDecisionSerializer,
    LicenceRefusalCriteriaSerializer,
    UnitSerializer,
)
from api.licences.enums import LicenceStatus
from api.licences.models import GoodOnLicence
from api.staticdata.countries.models import Country
from api.staticdata.denial_reasons.models import DenialReason
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.units.enums import Units


class BaseViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)

    @property
    def pagination_class(self):
        # Your pagination class should be a cursor pagination based class.
        # This is to avoid the issue where DW ends up losing or duplicating data
        # when a query doesn't return consistent results across pages.
        #
        # It is also highly recommended that you read the DRF documentation
        # about cursor based pagination so that you correctly pick the correct
        # type of field to order on.
        raise NotImplementedError("You must provide a pagination class that is ideally a cursor paginator.")


class LicenceDecisionViewSet(BaseViewSet):
    pagination_class = CreatedAtCursorPagination
    serializer_class = LicenceDecisionSerializer
    queryset = (
        LicenceDecision.objects.filter(previous_decision__isnull=True)
        .exclude(excluded_from_statistics_reason__isnull=False)
        .prefetch_related(
            Prefetch(
                "case__licence_decisions",
                queryset=LicenceDecision.objects.exclude(excluded_from_statistics_reason__isnull=False)
                .select_related("licence")
                .order_by("-created_at"),
                to_attr="unexcluded_licence_decisions",
            ),
        )
        .select_related("case")
    )

    class DataWorkspace:
        table_name = "licence_decisions"


class CountryViewSet(BaseViewSet):
    pagination_class = LimitOffsetPagination
    serializer_class = CountrySerializer
    queryset = Country.objects.all().order_by("id", "name")

    class DataWorkspace:
        table_name = "countries"


class DestinationViewSet(BaseViewSet):
    pagination_class = CreatedAtCursorPagination
    serializer_class = DestinationSerializer
    queryset = (
        PartyOnApplication.objects.filter(deleted_at__isnull=True)
        .exclude(application__status__status=CaseStatusEnum.DRAFT)
        .select_related("party", "party__country")
    )

    class DataWorkspace:
        table_name = "destinations"


class GoodViewSet(BaseViewSet):
    pagination_class = CreatedAtCursorPagination
    serializer_class = GoodSerializer
    queryset = GoodOnApplication.objects.exclude(application__status__status=CaseStatusEnum.DRAFT)

    class DataWorkspace:
        table_name = "goods"


class AssessmentDateCursorPagination(CursorPagination):
    ordering = "assessment_date"


class GoodDescriptionViewSet(BaseViewSet):
    pagination_class = AssessmentDateCursorPagination
    serializer_class = GoodDescriptionSerializer
    queryset = GoodOnApplication.objects.exclude(report_summaries__isnull=True).annotate(
        report_summary_prefix_name=F("report_summaries__prefix__name"),
        report_summary_subject_name=F("report_summaries__subject__name"),
    )

    class DataWorkspace:
        table_name = "goods_descriptions"


def get_closed_statuses():
    status_map = dict(CaseStatusEnum.choices)
    return list(
        itertools.chain.from_iterable((status, status_map[status]) for status in CaseStatusEnum.closed_statuses())
    )


class GoodOnLicenceViewSet(BaseViewSet):
    pagination_class = CreatedAtCursorPagination
    serializer_class = GoodOnLicenceSerializer
    queryset = GoodOnLicence.objects.exclude(
        licence__case__status__status=CaseStatusEnum.DRAFT,
        licence__status=LicenceStatus.DRAFT,
    )

    class DataWorkspace:
        table_name = "goods_on_licences"


class ApplicationViewSet(BaseViewSet):
    pagination_class = CreatedAtCursorPagination
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


class UnitViewSet(BaseViewSet):
    pagination_class = LimitOffsetPagination
    serializer_class = UnitSerializer
    queryset = [{"code": code, "description": description} for code, description in Units.choices]

    class DataWorkspace:
        table_name = "units"


class FootnoteViewSet(BaseViewSet):
    pagination_class = LimitOffsetPagination
    serializer_class = FootnoteSerializer
    queryset = (
        Advice.objects.exclude(Q(footnote="") | Q(footnote__isnull=True))
        .values("footnote", "team__name", "case__pk", "type")
        .order_by("case__pk")
        .distinct()
    )

    class DataWorkspace:
        table_name = "footnotes"


class GoodRatingViewSet(BaseViewSet):
    pagination_class = AssessmentDateCursorPagination
    serializer_class = GoodRatingSerializer
    queryset = GoodOnApplication.objects.exclude(control_list_entries__isnull=True).annotate(
        rating=F("control_list_entries__rating")
    )

    class DataWorkspace:
        table_name = "goods_ratings"


class LicenceRefusalCriteriaViewSet(BaseViewSet):
    pagination_class = LimitOffsetPagination
    serializer_class = LicenceRefusalCriteriaSerializer
    queryset = DenialReason.objects.exclude(licencedecision__denial_reasons__isnull=True).annotate(
        licence_decision_id=F("licencedecision__id")
    )

    class DataWorkspace:
        table_name = "licence_refusal_criteria"
