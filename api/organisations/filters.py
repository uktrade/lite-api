from rest_framework import filters


class OrganisationFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(organisation_id=view.kwargs["pk"])
