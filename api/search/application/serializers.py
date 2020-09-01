from django_elasticsearch_dsl_drf.serializers import DocumentSerializer

from api.search.application.documents import ApplicationDocumentType


class ApplicationDocumentSerializer(DocumentSerializer):
    class Meta:
        document = ApplicationDocumentType
        fields = (
            "id",
            "quantity",
            "value",
            "unit",
            "item_type",
            "incorporated",
            "good",
            "application",
            "parties"
        )
