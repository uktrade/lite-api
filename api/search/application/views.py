from django_elasticsearch_dsl_drf import filter_backends
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from elasticsearch_dsl.query import Query
from rest_framework.response import Response
from rest_framework.views import APIView
from django_elasticsearch_dsl_drf.constants import (
    LOOKUP_FILTER_TERMS,
    LOOKUP_FILTER_PREFIX,
    LOOKUP_FILTER_WILDCARD,
    LOOKUP_FILTER_RANGE,
    LOOKUP_QUERY_GT,
    LOOKUP_QUERY_GTE,
    LOOKUP_QUERY_LT,
    LOOKUP_QUERY_LTE,
)

from django.conf import settings

from api.search.application.backends import WildcardAwareSearchFilterBackend, WildcardAwareFilteringFilterBackend
from api.search.application.documents import ApplicationDocumentType
from api.search.application.serializers import ApplicationDocumentSerializer
from api.core.authentication import GovAuthentication


class MatchBoolPrefix(Query):
    name = "match_bool_prefix"


class ApplicationDocumentView(DocumentViewSet):
    document = ApplicationDocumentType
    serializer_class = ApplicationDocumentSerializer
    authentication_classes = (GovAuthentication,)
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
        "case_reference": {"enabled": True, "field": "reference_code.raw",},
        "case_status": {"enabled": True, "field": "status.raw",},
        "created": {
            "enabled": True,
            "field": "created",
            "lookups": [LOOKUP_FILTER_RANGE, LOOKUP_QUERY_GT, LOOKUP_QUERY_GTE, LOOKUP_QUERY_LT, LOOKUP_QUERY_LTE,],
        },
        "updated": {
            "enabled": True,
            "field": "updated",
            "lookups": [LOOKUP_FILTER_RANGE, LOOKUP_QUERY_GT, LOOKUP_QUERY_GTE, LOOKUP_QUERY_LT, LOOKUP_QUERY_LTE,],
        },
        "wildcard": {
            "field": "wildcard",
            "lookups": [LOOKUP_FILTER_TERMS, LOOKUP_FILTER_PREFIX, LOOKUP_FILTER_WILDCARD,],
        },
    }

    nested_filter_fields = {
        "clc_rating": {"field": "goods.control_list_entries.rating.raw", "path": "goods.control_list_entries",},
        "clc_category": {"field": "goods.control_list_entries.category.raw", "path": "goods.control_list_entries",},
        "party_country": {"field": "parties.country.raw", "path": "parties",},
        "party_type": {"field": "parties.type.raw", "path": "parties"},
        "part": {"field": "goods.part_number.raw", "path": "goods",},
        "incorporated": {"field": "goods.incorporated", "path": "goods",},
        "queue": {"field": "queues.name.raw", "path": "queues",},
        "team": {"field": "queues.team.raw", "path": "queues",},
        "case_officer_username": {"field": "case_officer.username.raw", "path": "case_officer",},
        "case_officer_email": {"field": "case_officer.email.raw", "path": "case_officer",},
    }

    highlight_fields = {"*": {"enabled": True, "options": {"pre_tags": ["<b>"], "post_tags": ["</b>"]}}}

    # Define ordering fields
    ordering_fields = {
        "id": None,
    }
    # Specify default ordering
    ordering = ("id",)

    def get_search_indexes(self):
        if self.request.GET.get('database') in settings.LITE_ELASTICSEARCH_INDEXES:
            return settings.LITE_ELASTICSEARCH_INDEXES[self.request.GET['database']]
        return list(settings.LITE_ELASTICSEARCH_INDEXES.values())

    def get_queryset(self):
        self.search._index = self.get_search_indexes()
        return super().get_queryset()


class ApplicationSuggestDocumentView(APIView):
    allowed_http_methods = ["get"]
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        q = self.request.GET.get("q", "")
        query = {
            "size": 5,
            "query": {"match_bool_prefix": {"wildcard": {"query": q}}},
            "suggest": {
                "party_country": {
                    "prefix": q,
                    "completion": {"field": "parties.country.suggest", "skip_duplicates": True},
                },
                "party_type": {"prefix": q, "completion": {"field": "parties.type.suggest", "skip_duplicates": True},},
                "clc_rating": {
                    "prefix": q,
                    "completion": {"field": "goods.control_list_entries.rating.suggest", "skip_duplicates": True},
                },
                "clc_category": {
                    "prefix": q,
                    "completion": {"field": "goods.control_list_entries.category.suggest", "skip_duplicates": True},
                },
                "part": {"prefix": q, "completion": {"field": "goods.part_number.suggest", "skip_duplicates": True},},
                "organisation": {
                    "prefix": q,
                    "completion": {"field": "organisation.suggest", "skip_duplicates": True},
                },
                "case_status": {"prefix": q, "completion": {"field": "status.suggest", "skip_duplicates": True},},
                "case_reference": {
                    "prefix": q,
                    "completion": {"field": "reference_code.suggest", "skip_duplicates": True},
                },
                "queue": {"prefix": q, "completion": {"field": "queues.name.suggest", "skip_duplicates": True},},
                "team": {"prefix": q, "completion": {"field": "queues.team.suggest", "skip_duplicates": True},},
                "case_officer_username": {
                    "prefix": q,
                    "completion": {"field": "case_officer.username.suggest", "skip_duplicates": True},
                },
                "case_officer_email": {
                    "prefix": q,
                    "completion": {"field": "case_officer.email.suggest", "skip_duplicates": True},
                },
            },
            "_source": False,
            "highlight": {"fields": {"wildcard": {"pre_tags": [""], "post_tags": [""]}}},
        }

        search = ApplicationDocumentType.search().from_dict(query)
        search._index = [ApplicationDocumentType.Index.name, settings.SPIRE_APPLICATION_INDEX_NAME]
        suggests = []
        executed = search.execute()
        flat_suggestions = set()

        for key in query["suggest"].keys():
            for suggest in getattr(executed.suggest, key):
                for option in suggest.options:
                    suggests.append(
                        {"field": key, "value": option.text, "index": "spire" if "spire" in option._index else "lite"}
                    )
                    flat_suggestions.add(option.text)

        for hit in executed:
            for option in hit.meta.highlight.wildcard:
                if option not in flat_suggestions:
                    suggests.append(
                        {
                            "field": "wildcard",
                            "value": option,
                            "index": "spire" if "spire" in hit.meta.index else "lite",
                        }
                    )
                    flat_suggestions.add(option)

        return Response(suggests)
