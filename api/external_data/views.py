from elasticsearch_dsl import Search
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from django_elasticsearch_dsl_drf import filter_backends
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

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
        filter_backends.SearchFilterBackend,
        filter_backends.SourceBackend,
        filter_backends.FilteringFilterBackend,
        filter_backends.HighlightBackend,
    ]
    search_fields = ["name", "address"]
    filter_fields = {
        "country": {
            "enabled": True,
            "field": "country.raw",
        }
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
    }

    def filter_queryset(self, queryset):
        # country = self.request.query_params.get("country", None)
        queryset = queryset.filter("term", is_revoked=False).exclude("term", notifying_government="United Kingdom")
        # .update(country=f"<mark>{country}</mark>")
        return super().filter_queryset(queryset)


class SanctionSearchView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        search = Search(index=settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS)
        results = search.query("match", name=request.GET["name"]).execute()
        return Response(results)
