from django_elasticsearch_dsl_drf.filter_backends import BaseSearchFilterBackend

from api.search.product.query_backends import QueryStringQueryBackend


class QueryStringSearchFilterBackend(BaseSearchFilterBackend):
    """
    Query string search filter backend.

    This adds support for the 'query_type' queries to the search plugin.
    The backend implements the methods to generate the query.
    """

    search_param = "search"

    query_backends = [
        QueryStringQueryBackend,
    ]
