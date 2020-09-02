from django_elasticsearch_dsl_drf.serializers import DocumentSerializer

from api.search.application.documents import ApplicationDocumentType


class ApplicationDocumentSerializer(DocumentSerializer):
    class Meta:
        document = ApplicationDocumentType
        fields = (
            "id",
            "reference_code",
            "case_type",
            "organisation",
            "status",
            "products",
            "parties",
        )
