from rest_framework import filters

from api.organisations.libraries.get_organisation import get_request_user_organisation


class CurrentExporterUserOrganisationFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        organisation = get_request_user_organisation(request)
        return queryset.filter(organisation=organisation)
