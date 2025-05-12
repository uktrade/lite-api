from rest_framework import filters
from api.cases.enums import CaseTypeSubTypeEnum


class F680CaseFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(case__case_type__sub_type=CaseTypeSubTypeEnum.F680)


class CurrentCaseFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(case_id=view.kwargs["pk"])
