from rest_framework import filters

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class DraftApplicationFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        draft_status = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return queryset.filter(status=draft_status)
