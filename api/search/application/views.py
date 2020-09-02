# Create your views here.
from django_elasticsearch_dsl_drf.filter_backends import (
    OrderingFilterBackend,
    SearchFilterBackend,
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
    ]
    # Define search fieldssearch
    search_fields = (
        "reference_code",
        "case_type",
        "organisation",
        "status",
        "products.good.part_number",
        "products.good.description",
        "parties.party.name",
        "wildcard",
    )


    # Define ordering fields
    ordering_fields = {
        "id": None,
    }
    # Specify default ordering
    ordering = ("id",)
