from django_elasticsearch_dsl_drf.filter_backends import BaseSearchFilterBackend

from api.search.product.query_backends import QueryStringQueryBackend


class QueryStringSearchFilterBackend(BaseSearchFilterBackend):
    """Query string search filter backend."""

    search_param = "search"

    query_backends = [
        QueryStringQueryBackend,
    ]
