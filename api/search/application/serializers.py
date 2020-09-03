from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from django_elasticsearch_dsl_drf.fields import NestedField

from api.search.application import documents


class ApplicationDocumentSerializer(DocumentSerializer):
    class Meta:
        document = documents.ApplicationDocumentType
        fields = (
            "id",
            "reference_code",
            "case_type",
            "organisation",
            "status",
            "goods",
            "parties",
            "destinations",
        )

    _field_mapping = {
        **DocumentSerializer._field_mapping,
        documents.OpenApplicationNestedField: NestedField,
    }
