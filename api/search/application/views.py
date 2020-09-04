from django_elasticsearch_dsl_drf.constants import (
    LOOKUP_FILTER_TERMS,
    LOOKUP_FILTER_PREFIX,
    LOOKUP_FILTER_WILDCARD,
)
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    NestedFilteringFilterBackend,
)

from django_elasticsearch_dsl_drf.viewsets import BaseDocumentViewSet

from api.search.application.backends import LiteCustomSearchFilterBackend, LiteCustomFilteringFilterBackend
from api.search.application.documents import ApplicationDocumentType
from api.search.application.serializers import ApplicationDocumentSerializer


class ApplicationDocumentView(BaseDocumentViewSet):
    document = ApplicationDocumentType
    serializer_class = ApplicationDocumentSerializer
    lookup_field = "id"
    filter_backends = [
        LiteCustomSearchFilterBackend,
        LiteCustomFilteringFilterBackend,
        OrderingFilterBackend,
        NestedFilteringFilterBackend,
    ]

    # Define search fieldssearch
    search_fields = {
        "wildcard": None,
    }

    filter_fields = {
        "wildcard": {
            "field": "wildcard",
            "lookups": [LOOKUP_FILTER_TERMS, LOOKUP_FILTER_PREFIX, LOOKUP_FILTER_WILDCARD,],
        }
    }

    nested_filter_fields = {
        "clc_rating": {"field": "goods.good.control_list_entries.rating", "path": "goods.good.control_list_entries",},
    }

    # Define ordering fields
    ordering_fields = {
        "id": None,
    }
    # Specify default ordering
    ordering = ("id",)
