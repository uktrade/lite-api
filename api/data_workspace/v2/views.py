import itertools

from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from django.db.models import (
    F,
    Min,
    Q,
)
from django.db.models.query import QuerySet
from django.http import Http404

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
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.core.helpers import str_to_bool
from api.data_workspace.v2.serializers import (
    ApplicationSerializer,
    CountrySerializer,
    DestinationSerializer,
    FootnoteSerializer,
    GoodDescriptionSerializer,
    GoodOnLicenceSerializer,
    GoodSerializer,
    GoodRatingSerializer,
    LicenceDecisionSerializer,
    LicenceRefusalCriteriaSerializer,
    StatusSerializer,
    UnitSerializer,
)
from api.licences.enums import LicenceStatus
from api.licences.models import GoodOnLicence
from api.staticdata.control_list_entries.models import ControlListEntry
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


class ApplicationViewSet(BaseViewSet):
    serializer_class = ApplicationSerializer
    queryset = (
        StandardApplication.objects.exclude(status__status=CaseStatusEnum.DRAFT)
        .select_related("case_type", "status")
        .prefetch_related("goods", "licence_decisions")
    )

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


class CountryViewSet(BaseViewSet):
    serializer_class = CountrySerializer
    queryset = Country.objects.all().order_by("id", "name")


class DestinationViewSet(BaseViewSet):
    serializer_class = DestinationSerializer
    queryset = (
        PartyOnApplication.objects.filter(deleted_at__isnull=True)
        .exclude(application__status__status=CaseStatusEnum.DRAFT)
        .select_related("party", "party__country")
    )


class GoodViewSet(BaseViewSet):
    serializer_class = GoodSerializer
    queryset = GoodOnApplication.objects.exclude(application__status__status=CaseStatusEnum.DRAFT)


class GoodRatingViewSet(BaseViewSet):
    serializer_class = GoodRatingSerializer
    queryset = ControlListEntry.objects.annotate(good_id=F("goodonapplication__id")).exclude(good_id__isnull=True)


class GoodDescriptionViewSet(BaseViewSet):
    serializer_class = GoodDescriptionSerializer
    queryset = (
        ReportSummary.objects.select_related("prefix", "subject")
        .prefetch_related("goods_on_application")
        .exclude(goods_on_application__isnull=True)
        .annotate(good_id=F("goods_on_application__id"))
    )


class GoodOnLicenceViewSet(BaseViewSet):
    serializer_class = GoodOnLicenceSerializer
    queryset = GoodOnLicence.objects.exclude(
        licence__case__status__status=CaseStatusEnum.DRAFT,
        licence__status=LicenceStatus.DRAFT,
    )


class LicenceRefusalCriteriaViewSet(BaseViewSet):
    serializer_class = LicenceRefusalCriteriaSerializer
    queryset = (
        Advice.objects.filter(
            case__licence_decisions__decision="refused",
            team_id="58e77e47-42c8-499f-a58d-94f94541f8c6",  # Just care about LU advice
        )
        .only("denial_reasons__display_value", "case__licence_decisions__id")
        .exclude(denial_reasons__display_value__isnull=True)  # This removes refusals without any criteria
        .values("denial_reasons__display_value", "case__licence_decisions__id")
        .order_by()  # We need to remove the order_by to make sure the distinct works
        .distinct()
    )


class FootnoteViewSet(BaseViewSet):
    serializer_class = FootnoteSerializer
    queryset = (
        Advice.objects.exclude(Q(footnote="") | Q(footnote__isnull=True))
        .values("footnote", "team__name", "case__pk", "type")
        .order_by("case__pk")
        .distinct()
    )


class UnitViewSet(viewsets.ViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)

    def list(self, request):
        units = [{"code": code, "description": description} for code, description in Units.choices]
        return Response(UnitSerializer(units, many=True).data)

    def retrieve(self, request, pk):
        units = dict(Units.choices)
        try:
            description = units[pk]
        except KeyError:
            raise Http404()
        return Response(UnitSerializer({"code": pk, "description": description}).data)


class StatusViewSet(viewsets.ViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = DisableableLimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)

    def list(self, request):
        statuses = [{"status": status, "name": name} for status, name in CaseStatusEnum.choices]
        return Response(StatusSerializer(statuses, many=True).data)

    def retrieve(self, request, pk):
        statuses = dict(CaseStatusEnum.choices)
        try:
            name = statuses[pk]
        except KeyError:
            raise Http404()
        return Response(StatusSerializer({"status": pk, "name": name}).data)
