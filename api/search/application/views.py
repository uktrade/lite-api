from django_elasticsearch_dsl_drf.constants import SUGGESTER_COMPLETION, FUNCTIONAL_SUGGESTER_COMPLETION_MATCH
from django_elasticsearch_dsl_drf import filter_backends
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from elasticsearch_dsl.query import Query
from rest_framework.response import Response
from rest_framework.views import APIView
from django_elasticsearch_dsl_drf.constants import (
    LOOKUP_FILTER_TERMS,
    LOOKUP_FILTER_PREFIX,
    LOOKUP_FILTER_WILDCARD,
)

from api.search.application.backends import WildcardAwareSearchFilterBackend, WildcardAwareFilteringFilterBackend
from api.search.application.documents import ApplicationDocumentType
from api.search.application.serializers import ApplicationDocumentSerializer


class MatchBoolPrefix(Query):
    name = "match_bool_prefix"


class ApplicationDocumentView(DocumentViewSet):
    document = ApplicationDocumentType
    serializer_class = ApplicationDocumentSerializer
    lookup_field = "id"
    filter_backends = [
        filter_backends.OrderingFilterBackend,
        WildcardAwareSearchFilterBackend,
        WildcardAwareFilteringFilterBackend,
        filter_backends.NestedFilteringFilterBackend,
        filter_backends.SourceBackend,
        filter_backends.HighlightBackend,
    ]

    # Define search fieldssearch
    search_fields = [
        "wildcard",
        "organisation",
    ]

    search_nested_fields = {
        # explicitly defined to make highlighting work
        "good": {"path": "goods", "fields": ["description"]},
        "clc": {"path": "goods.control_list_entries", "fields": ["rating", "text", "parent"]},
    }

    filter_fields = {
        "organisation": {"enabled": True, "field": "organisation.raw",},
        "wildcard": {
            "field": "wildcard",
            "lookups": [LOOKUP_FILTER_TERMS, LOOKUP_FILTER_PREFIX, LOOKUP_FILTER_WILDCARD,],
        },
    }

    nested_filter_fields = {
        "rating": {"field": "goods.control_list_entries.rating.raw", "path": "goods.control_list_entries",},
        "destination": {"field": "parties.country.raw", "path": "parties",},
        "part": {"field": "goods.part_number.raw", "path": "goods",},
        "incorporated": {"field": "goods.incorporated", "path": "goods",},
    }

    highlight_fields = {"*": {"enabled": True, "options": {"pre_tags": ["<b>"], "post_tags": ["</b>"]}}}

    # Define ordering fields
    ordering_fields = {
        "id": None,
    }
    # Specify default ordering
    ordering = ("id",)


class ApplicationSuggestDocumentView(APIView):
    allowed_http_methods = ["get"]

    def get(self, request):
        q = self.request.GET.get("q", "")
        search = ApplicationDocumentType.search().from_dict(
            {
                "size": 5,
                "query": {"match_bool_prefix": {"wildcard": {"query": q}}},
                "suggest": {
                    "destination": {
                        "prefix": q,
                        "completion": {"field": "parties.country.suggest", "skip_duplicates": True},
                    },
                    "rating": {
                        "prefix": q,
                        "completion": {"field": "goods.control_list_entries.rating.suggest", "skip_duplicates": True},
                    },
                    "part": {
                        "prefix": q,
                        "completion": {"field": "goods.part_number.suggest", "skip_duplicates": True},
                    },
                    "organisation": {
                        "prefix": q,
                        "completion": {"field": "organisation.suggest", "skip_duplicates": True},
                    },
                },
                "_source": False,
                "highlight": {"fields": {"wildcard": {"pre_tags": [""], "post_tags": [""]}}},
            }
        )

        suggests = []
        executed = search.execute()
        flat_suggestions = set()

        for key in ["destination", "rating", "part", "organisation"]:
            for suggest in getattr(executed.suggest, key):
                for option in suggest.options:
                    suggests.append({"field": key, "value": option.text})
                    flat_suggestions.add(option.text)

        for hit in executed:
            for option in hit.meta["highlight"]["wildcard"]:
                if option not in flat_suggestions:
                    suggests.append({"field": "wildcard", "value": option})
                    flat_suggestions.add(option)

        return Response(suggests)
