# Create your views here.
from django_elasticsearch_dsl_drf.constants import SUGGESTER_COMPLETION
from django_elasticsearch_dsl_drf.filter_backends import (
    OrderingFilterBackend,
    SearchFilterBackend,
    NestedFilteringFilterBackend,
    SuggesterFilterBackend,
    SourceBackend,
)

from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

# Example app models
from api.search.application.documents import ApplicationDocumentType
from api.search.application.serializers import ApplicationDocumentSerializer


class ApplicationDocumentView(DocumentViewSet):
    document = ApplicationDocumentType
    serializer_class = ApplicationDocumentSerializer
    lookup_field = "id"
    filter_backends = [
        OrderingFilterBackend,
        SearchFilterBackend,
        NestedFilteringFilterBackend,
        SuggesterFilterBackend,
        SourceBackend,
    ]

    # Define search fieldssearch
    search_fields = {
        "wildcard.raw": None,
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

    # Suggester fields
    suggester_fields = {
        'wildcard_suggest': {
            'field': 'wildcard.suggest',
            'default_suggester': SUGGESTER_COMPLETION,
            'options': {
                'skip_duplicates': True,
            },
        },
    }

    # Define ordering fields
    ordering_fields = {
        "id": None,
    }
    # Specify default ordering
    ordering = ("id",)

    @property
    def source(self):
        return self.request.GET.get('source', 'true') == 'true'
