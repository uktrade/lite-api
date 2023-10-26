from django_elasticsearch_dsl_drf import filter_backends
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from elasticsearch_dsl.query import Query

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView

from django.conf import settings

from api.search.product.documents import ProductDocumentType
from api.search.product import serializers
from api.search import models
from api.core.authentication import GovAuthentication


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
        filter_backends.SimpleQueryStringSearchFilterBackend,
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
    ]

    simple_query_string_search_fields = {
        "name": None,
        "part_number": None,
        "control_list_entries": None,
        "report_summary": None,
    }

    simple_query_string_options = {"default_operator": "or"}

    search_nested_fields = {
        # explicitly defined to make highlighting work
        "clc": {"path": "control_list_entries", "fields": ["rating", "text", "parent"]},
        "assessed_by": {"path": "assessed_by", "fields": ["first_name", "last_name", "email"]},
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

    def get_queryset(self):
        query_params = self.request.GET.copy()
        query = query_params.getlist("search", [""])
        query_type = query_params.get("query_type", "simple_query_string")

        if query_type == "simple_query_string":
            self.filter_backends[2].search_param = "search"

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
                                "rating_comment": self.highlight_fields["*"]["options"],
                            }
                        },
                    },
                }
            }
        )

        if query_type == "query_string":
            self.search.update_from_dict(
                {
                    "query": {
                        "query_string": {
                            "query": query[0],
                            "fields": ["name", "report_summary", "part_number", "control_list_entries", "wildcard"],
                        }
                    }
                }
            )

        return super().get_queryset()


class ProductSuggestDocumentView(APIView):
    allowed_http_methods = ["get"]
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        q = self.request.GET.get("q", "")
        query = {
            "size": 5,
            "query": {"match_bool_prefix": {"wildcard": {"query": q}}},
            "suggest": {
                "clc_rating": {
                    "prefix": q,
                    "completion": {"field": "control_list_entries.rating.suggest", "skip_duplicates": True},
                },
                "organisation": {
                    "prefix": q,
                    "completion": {"field": "organisation.suggest", "skip_duplicates": True},
                },
                "destination": {
                    "prefix": q,
                    "completion": {"field": "destination.suggest", "skip_duplicates": True},
                },
            },
            "_source": False,
            "highlight": {"fields": {"wildcard": {"pre_tags": [""], "post_tags": [""]}}},
        }

        search = ProductDocumentType.search().from_dict(query)
        search._index = list(settings.ELASTICSEARCH_PRODUCT_INDEXES.values())
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


class MoreLikeThisView(APIView):
    allowed_http_methods = ["get"]
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        document = ProductDocumentType.get(id=pk, ignore=404)
        if not document:
            return Response([])
        search = ProductDocumentType.search()
        search._index = list(settings.ELASTICSEARCH_PRODUCT_INDEXES.values())
        search = (
            search.filter("term", canonical_name=document.canonical_name)
            .exclude("match", id=pk)
            .update_from_dict({"collapse": {"field": "application.id"}})
        )
        serializer = serializers.ProductDocumentSerializer(search, many=True)
        return Response(serializer.data)


class AbstractRetrieveLiteProductView(APIView):
    allowed_http_methods = ["get"]
    authentication_classes = (GovAuthentication,)
    index_name = None

    def get(self, request, pk):
        class Document(ProductDocumentType):
            class Index(ProductDocumentType.Index):
                name = self.index_name

        product = Document.get(id=pk)
        product_serializer = serializers.ProductDocumentSerializer(product)

        related_products = Document.search().filter("term", canonical_name=product.canonical_name)
        related_products_serializer = serializers.ProductDocumentSerializer(related_products, many=True)

        comments = models.Comment.objects.filter(object_pk=pk).order_by("-updated_at")
        comments_serializer = serializers.CommentSerializer(comments, many=True)

        return Response(
            {
                "related_products": related_products_serializer.data,
                "comments": comments_serializer.data,
                **product_serializer.data,
            }
        )


class RetrieveLiteProductView(AbstractRetrieveLiteProductView, APIView):
    index_name = settings.ELASTICSEARCH_PRODUCT_INDEX_ALIAS


class RetrieveSpireProductView(AbstractRetrieveLiteProductView, APIView):
    index_name = settings.SPIRE_PRODUCT_INDEX_NAME


class CommentView(CreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = serializers.CommentSerializer
