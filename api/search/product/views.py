from django_elasticsearch_dsl_drf import filter_backends
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from elasticsearch_dsl.query import Query

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveAPIView

from django.conf import settings
from django.db.models import Case, When
from django.db.models.fields import IntegerField
from django.http import JsonResponse

from api.core.authentication import GovAuthentication
from api.search import models
from api.search.product.documents import ProductDocumentType
from api.search.product import serializers
from api.search.product import filter_backends as custom_filter_backends

from collections import OrderedDict


class MatchBoolPrefix(Query):
    name = "match_bool_prefix"


class ProductDocumentView(DocumentViewSet):
    document = ProductDocumentType
    serializer_class = serializers.ProductDocumentSerializer
    authentication_classes = (GovAuthentication,)
    lookup_field = "id"
    filter_backends = [
        filter_backends.OrderingFilterBackend,
        filter_backends.DefaultOrderingFilterBackend,
        custom_filter_backends.QueryStringSearchFilterBackend,
        filter_backends.FilteringFilterBackend,
        filter_backends.NestedFilteringFilterBackend,
        filter_backends.SourceBackend,
        filter_backends.HighlightBackend,
    ]

    search_fields = [
        "name",
        "part_number",
        "control_list_entries",
        "report_summary",
        "organisation",
        "assessment_note",
        "consignee_country",
        "end_user_country",
        "ultimate_end_user_country",
    ]

    query_string_search_fields = {
        "name": None,
        "part_number": None,
        "report_summary": None,
        "organisation": None,
        "assessment_note": None,
        "ratings": None,
        "regimes": None,
        "assessed_by": None,
        "consignee_country": None,
        "end_user_country": None,
        "ultimate_end_user_country": None,
    }

    search_nested_fields = {
        # explicitly defined to make highlighting work
        "clc": {"path": "control_list_entries", "fields": ["rating", "text", "parent"]},
        "regime_entries": {"path": "regime_entries", "fields": ["shortened_name", "name"]},
    }

    filter_fields = {
        "organisation": {"enabled": True, "field": "organisation.raw"},
        "destination": {"enabled": True, "field": "destination.raw"},
        "canonical_name": {"enabled": True, "field": "canonical_name"},
    }

    nested_filter_fields = {
        "clc_rating": {"field": "control_list_entries.rating.raw", "path": "control_list_entries"},
        "clc_category": {"field": "control_list_entries.category.raw", "path": "control_list_entries"},
    }

    # define ordering fields
    ordering_fields = {"assessment_date": "assessment_date"}

    # specify default ordering
    ordering = ("-assessment_date",)

    highlight_fields = {"*": {"enabled": True, "options": {"pre_tags": ["<b>"], "post_tags": ["</b>"]}}}

    def get_search_indexes(self):
        if self.request.GET.get("database") in settings.ELASTICSEARCH_PRODUCT_INDEXES:
            return settings.ELASTICSEARCH_PRODUCT_INDEXES[self.request.GET["database"]]
        return list(settings.ELASTICSEARCH_PRODUCT_INDEXES.values())

    def validate_search_terms(self):
        query_params = self.request.GET.copy()
        search_term = query_params.get("search")

        # Validation is only required if we are using QueryStringSearchFilterBackend
        if custom_filter_backends.QueryStringSearchFilterBackend not in self.filter_backends:
            return True

        # create a query with the given query params
        query = {
            "query": {
                "query_string": {
                    "fields": ["*"],
                    "query": f"{search_term}",
                }
            }
        }
        response = self.document._index.validate_query(body=query)
        return response["valid"]

    def dispatch(self, request, *args, **kwargs):
        self.search._index = self.get_search_indexes()
        if not self.validate_search_terms():
            return JsonResponse(
                data={
                    "error": "Invalid search string",
                    "results": [],
                    "count": 0,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.search._index = self.get_search_indexes()
        self.search.update_from_dict(
            {
                "collapse": {
                    "field": "canonical_name",
                    "inner_hits": {
                        "size": 200,
                        "name": "related",
                        "collapse": {
                            "field": "context",
                        },
                        "sort": [
                            {
                                "assessment_date": {
                                    "order": "desc",
                                },
                            }
                        ],
                        "highlight": {
                            "fields": {
                                "assessment_note": self.highlight_fields["*"]["options"],
                            }
                        },
                    },
                }
            }
        )
        queryset = super().get_queryset()
        return queryset

    def get_model_queryset(self, document_queryset):
        pks = [result.meta.id for result in document_queryset]
        qs = self.document.Django.model.objects.filter(pk__in=pks)
        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pks)], output_field=IntegerField())
        qs = qs.order_by(preserved_order)
        return qs

    def augment_hits_with_instances(self, hits):
        qs = self.get_model_queryset(hits)

        for hit, instance in zip(hits, qs):
            hit.instance = instance

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            self.augment_hits_with_instances(page)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        self.augment_hits_with_instances(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductSuggestDocumentView(RetrieveAPIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        query_str = self.request.GET.get("q", "")

        query = {
            "size": 30,
            "query": {
                "multi_match": {
                    "query": query_str,
                    "type": "bool_prefix",
                    "fields": [
                        "name",
                        "part_number",
                        "ratings",
                        "regimes",
                        "report_summary",
                        "organisation",
                        "assessed_by",
                        "consignee_country",
                        "end_user_country",
                        "ultimate_end_user_country",
                        "assessment_note",
                    ],
                }
            },
            "highlight": {
                "fields": {
                    "*": {
                        "post_tags": [""],
                        "pre_tags": [""],
                    },
                },
            },
            "_source": False,
        }

        search = ProductDocumentType.search().from_dict(query)
        search._index = list(settings.ELASTICSEARCH_PRODUCT_INDEXES.values())
        response = search.execute()

        suggestions = OrderedDict()
        for hit in response.hits:
            for field, value in hit.meta.highlight.to_dict().items():
                value = value[0]
                suggestion = {
                    "field": field,
                    "value": value,
                    "index": "spire" if "spire" in hit.meta.index else "lite",
                }
                suggestions[tuple(suggestion.items())] = suggestion

        return Response(list(suggestions.values()))
