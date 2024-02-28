from rest_framework import filters


class AppealFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(appeal_id=view.kwargs["pk"])
