from django.forms import ValidationError
from elasticsearch_dsl import Search
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from django_elasticsearch_dsl_drf import filter_backends
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from api.core.search import filter_backends as custom_filter_backends

from django.conf import settings

from api.core.authentication import GovAuthentication
from api.conf.pagination import MaxPageNumberPagination
from api.external_data import documents, models, serializers


class DenialViewSet(viewsets.ModelViewSet):
    queryset = models.DenialEntity.objects.all()
    authentication_classes = (GovAuthentication,)

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.DenialFromCSVFileSerializer
        return serializers.DenialEntitySerializer

    def perform_create(self, serializer):
        pass


class SanctionViewSet(viewsets.ModelViewSet):
    authentication_classes = (GovAuthentication,)
    serializer_class = serializers.SanctionMatchSerializer
    queryset = models.SanctionMatch.objects.all()

    def perform_create(self, serializer):
        pass


class DenialSearchView(DocumentViewSet):
    document = documents.DenialEntityDocument
    serializer_class = serializers.DenialSearchSerializer
    authentication_classes = (GovAuthentication,)
    pagination_class = MaxPageNumberPagination
    lookup_field = "id"
    filter_backends = [
        filter_backends.SourceBackend,
        filter_backends.FilteringFilterBackend,
        custom_filter_backends.QueryStringSearchFilterBackend,
        filter_backends.HighlightBackend,
    ]

<<<<<<< HEAD
    search_fields = ["name", "address", "denial_cle"]
=======
    search_fields = ["name", "address" "item_list_codes"]
>>>>>>> 76174110 (refactor)

    filter_fields = {
        "country": {
            "enabled": True,
            "field": "country.raw",
        }
    }

    query_string_search_fields = {
        "name": None,
        "address": None,
        "item_list_codes": None,
    }

    ordering = "_score"
    highlight_fields = {
        "name": {
            "enabled": True,
            "options": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
            },
        },
        "address": {
            "enabled": True,
            "options": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
            },
        },
        "denial_cle": {
            "enabled": True,
            "options": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
            },
        },
    }

    def filter_queryset(self, queryset):
        queryset = queryset.filter("term", is_revoked=False).exclude("term", notifying_government="United Kingdom")
        qs = super().filter_queryset(queryset)
        print(qs.to_dict())
        return super().filter_queryset(queryset)

    def validate_search_terms(self):
        query_params = self.request.GET.copy()
        search_term = query_params.get("search")

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

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not self.validate_search_terms():
            raise ValidationError({"search": "Invalid search string"})


class SanctionSearchView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        search = Search(index=settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS)
        results = search.query("match", name=request.GET["name"]).execute()
        return Response(results)
