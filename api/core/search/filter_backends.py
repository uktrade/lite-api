from django_elasticsearch_dsl_drf.filter_backends import BaseSearchFilterBackend

from .query_backends import QueryStringQueryBackend


class QueryStringSearchFilterBackend(BaseSearchFilterBackend):
    """
    Query string search filter backend.

    This adds support for the 'query_type' queries to the search plugin.
    The backend implements the methods to generate the query.
    """

    search_param = "search"

    def get_search_query_params(self, request):
        """Get search query params.

        :param request: Django REST framework request.
        :type request: rest_framework.request.Request
        :return: List of search query params.
        :rtype: list
        """
        query_params = request.query_params.copy()
        # This is required as query_string is unable to handle a single /
        query_string = query_params.get(self.search_param, "").replace("/", "//")
        query_params[self.search_param] = query_string
        return query_params.getlist(self.search_param, [])

    query_backends = [
        QueryStringQueryBackend,
    ]
