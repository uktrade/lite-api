from rest_framework import filters

from api.applications.models import SiteOnApplication
from api.organisations.libraries.get_organisation import get_request_user_organisation
from api.organisations.models import Site
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


class ApplicationSiteFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        organisation = get_request_user_organisation(request)
        users_sites = Site.objects.get_by_user_and_organisation(request.user.exporteruser, organisation)
        disallowed_applications = SiteOnApplication.objects.exclude(site__id__in=users_sites).values_list(
            "application", flat=True
        )
        queryset = queryset.exclude(id__in=disallowed_applications)

        return queryset


class ApplicationStateFilter(filters.BaseFilterBackend):
    FILTER_STATUS_MAP = {
        "draft_tab": CaseStatus.objects.filter(status=CaseStatusEnum.DRAFT),
        "draft_applications": CaseStatus.objects.filter(status=CaseStatusEnum.DRAFT),
        "submitted_applications": CaseStatus.objects.exclude(
            status__in=[
                CaseStatusEnum.DRAFT,
                CaseStatusEnum.FINALISED,
                CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT,
            ]
        ),
        "finalised_applications": CaseStatus.objects.filter(status=CaseStatusEnum.FINALISED),
        "archived_applications": CaseStatus.objects.filter(status=CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT),
    }

    def filter_queryset(self, request, queryset, view):
        selected_filter = request.GET.get("selected_filter", "submitted_applications")
        sort_by = request.GET.get("sort_by", "-submitted_at")

        organisation = get_request_user_organisation(request)

        statuses = self.FILTER_STATUS_MAP[selected_filter]
        queryset = queryset.filter(organisation=organisation, status__in=statuses).order_by(sort_by)

        return queryset.prefetch_related("status", "case_type").select_subclasses()
