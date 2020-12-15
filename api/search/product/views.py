from django_elasticsearch_dsl_drf import filter_backends
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from elasticsearch_dsl.query import Query, MoreLikeThis
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView

from django.conf import settings

from api.search.product.documents import ProductDocumentType
from api.search.product import models, serializers
from api.core.authentication import GovAuthentication


class MatchBoolPrefix(Query):
    name = "match_bool_prefix"


class ProductDocumentView(DocumentViewSet):
    document = ProductDocumentType
    serializer_class = serializers.ProductDocumentSerializer
    authentication_classes = (GovAuthentication,)
    lookup_field = "id"
    filter_backends = [
        filter_backends.SearchFilterBackend,
        filter_backends.FilteringFilterBackend,
        filter_backends.NestedFilteringFilterBackend,
        filter_backends.SourceBackend,
        filter_backends.HighlightBackend,
    ]

    search_fields = [
        "wildcard",
    ]

    search_nested_fields = {
        # explicitly defined to make highlighting work
        "clc": {"path": "control_list_entries", "fields": ["rating", "text", "parent"]},
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

    highlight_fields = {"*": {"enabled": True, "options": {"pre_tags": ["<b>"], "post_tags": ["</b>"]}}}

    def get_search_indexes(self):
        if self.request.GET.get("database") in settings.ELASTICSEARCH_PRODUCT_INDEXES:
            return settings.ELASTICSEARCH_PRODUCT_INDEXES[self.request.GET["database"]]
        return list(settings.ELASTICSEARCH_PRODUCT_INDEXES.values())

    def get_queryset(self):
        self.search._index = self.get_search_indexes()
        self.search.update_from_dict(
            {
                "collapse": {
                    "field": "canonical_name",
                    "inner_hits": {
                        "size": 200,
                        "name": "related",
                        "collapse": {"field": "context",},
                        "highlight": {"fields": {"rating_comment": self.highlight_fields["*"]["options"],}},
                    },
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
                "destination": {"prefix": q, "completion": {"field": "destination.suggest", "skip_duplicates": True},},
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
        document = ProductDocumentType.get(id=pk)
        search = ProductDocumentType.search()
        search._index = list(settings.ELASTICSEARCH_PRODUCT_INDEXES.values())
        search = (
            search
            .filter("term", canonical_name=document.canonical_name)
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

        document = Document.get(id=pk)

        search = Document.search().filter("term", canonical_name=document.canonical_name)
        related_products = search.execute()

        comments = models.Comment.objects.filter(object_pk=pk).order_by("-updated_at")

        return Response(
            {
                "related_products": [item["_source"] for item in related_products.to_dict()["hits"]["hits"]],
                "comments": serializers.CommentSerializer(comments, many=True).data,
                **document.to_dict(),
            }
        )


class RetrieveLiteProductView(AbstractRetrieveLiteProductView, APIView):
    index_name = settings.ELASTICSEARCH_PRODUCT_INDEX_ALIAS


class RetrieveSpireProductView(AbstractRetrieveLiteProductView, APIView):
    index_name = settings.SPIRE_PRODUCT_INDEX_NAME


class CommentView(CreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = serializers.CommentSerializer
