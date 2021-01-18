from rest_framework import viewsets
from rest_framework.response import Response

from django_elasticsearch_dsl_drf import filter_backends
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

from api.core.authentication import GovAuthentication
from api.external_data import documents, models, serializers


class DenialViewSet(viewsets.ModelViewSet):
    queryset = models.Denial.objects.all()
    authentication_classes = (GovAuthentication,)

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.DenialFromCSVFileSerializer
        return serializers.DenialSerializer

    def perform_create(self, serializer):
        pass


class DenialSearchView(DocumentViewSet):
    document = documents.DenialDocumentType
    serializer_class = serializers.DenialSearchSerializer
    authentication_classes = (GovAuthentication,)
    lookup_field = "id"
    filter_backends = [
        filter_backends.SearchFilterBackend,
        filter_backends.SourceBackend,
    ]
    search_fields = ["name", "address"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response(queryset.execute().to_dict())

    def filter_queryset(self, queryset):
        queryset = queryset.filter("term", is_revoked=False)
        return super().filter_queryset(queryset)
