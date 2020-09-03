# Create your views here.
from django_elasticsearch_dsl_drf.filter_backends import (
    OrderingFilterBackend,
    SearchFilterBackend,
    NestedFilteringFilterBackend,
)

from django_elasticsearch_dsl_drf.viewsets import BaseDocumentViewSet

# Example app models
from api.search.application.documents import ApplicationDocumentType
from api.search.application.serializers import ApplicationDocumentSerializer


class ApplicationDocumentView(BaseDocumentViewSet):
    document = ApplicationDocumentType
    serializer_class = ApplicationDocumentSerializer
    lookup_field = "id"
    filter_backends = [
        OrderingFilterBackend,
        SearchFilterBackend,
        NestedFilteringFilterBackend,
    ]

    # Define search fieldssearch
    search_fields = {
        "wildcard": None,
    }

    nested_filter_fields = {
        'clc': {
            'field': 'goods.good.control_list_entries.rating',
            'path': 'goods.good.control_list_entries',
        },
        'destination': {
            'field': 'destinations.name',
            'path': 'destinations',
        },
    }

    # Define ordering fields
    ordering_fields = {
        "id": None,
    }
    # Specify default ordering
    ordering = ("id",)
