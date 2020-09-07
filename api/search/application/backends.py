from rest_framework.settings import api_settings

from django_elasticsearch_dsl_drf.constants import SEPARATOR_LOOKUP_FILTER
from django_elasticsearch_dsl_drf.filter_backends import SearchFilterBackend, FilteringFilterBackend


def expand_search_params(params):
    expanded_params = []
    for p in params:
        expanded_params.extend(p.split(","))

    return expanded_params


def wildcard_present(params, wildcards=["?", "*"]):
    return any([char in p for char in wildcards for p in params])


class WildcardAwareSearchFilterBackend(SearchFilterBackend):
    def get_search_query_params(self, request):
        query_params = super().get_search_query_params(request)
        updated_params = expand_search_params(query_params)

        # if it is a wildcard search ignore as it will be handled by wildcard filter
        return [] if wildcard_present(updated_params) else updated_params


class WildcardAwareFilteringFilterBackend(FilteringFilterBackend):
    def get_filter_query_params(self, request, view):
        filter_params = super().get_filter_query_params(request, view)
        wildcard_param_key = f"wildcard{SEPARATOR_LOOKUP_FILTER}wildcard"

        """
        In the search box if wildcards (?, *) are entered by default they
        are searched as is, to actually perform wildcard search add
        wildcard filter using the search query param
        """
        query_params = request.query_params.copy()
        search_params = query_params.getlist(api_settings.SEARCH_PARAM, [])
        expanded_params = expand_search_params(search_params)

        if expanded_params:
            filter_params = {}
            if wildcard_present(expanded_params):
                filter_params = {
                    wildcard_param_key: {
                        "lookup": "wildcard",
                        "values": expanded_params,
                        "field": "wildcard",
                        "type": "properties",
                    }
                }

        return filter_params
