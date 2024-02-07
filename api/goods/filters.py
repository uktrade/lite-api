from rest_framework import filters


class GoodFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(good_id=view.kwargs["pk"])
