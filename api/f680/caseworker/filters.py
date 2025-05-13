from rest_framework import filters


class CurrentCaseFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(case_id=view.kwargs["pk"])
