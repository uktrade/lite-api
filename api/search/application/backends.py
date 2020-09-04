from django_elasticsearch_dsl_drf.filter_backends import SearchFilterBackend


class LiteCustomSearchFilterBackend(SearchFilterBackend):
    
    def get_search_query_params(self, request):
        query_params = super().get_search_query_params(request)
        updated_params = []
        for p in query_params:
            updated_params.extend(p.split(","))
        return updated_params
