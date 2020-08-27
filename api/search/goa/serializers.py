from django_elasticsearch_dsl_drf.serializers import DocumentSerializer

from api.search.goa.documents import GoodOnApplicationDocumentType


class GoodOnApplicationDocumentSerializer(DocumentSerializer):
    class Meta:
        document = GoodOnApplicationDocumentType
        fields = (
            "id",
            "quantity",
            "value",
            "unit",
            "item_type",
            "incorporated",
            "good",
            "application",
        )
