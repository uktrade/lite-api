from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from django_elasticsearch_dsl_drf.fields import NestedField
from rest_framework import serializers

from api.search.application import documents


class ApplicationDocumentSerializer(DocumentSerializer):
    highlight = serializers.SerializerMethodField()

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
            "name",
            "destinations",
            "highlight"
        )

    _field_mapping = {
        **DocumentSerializer._field_mapping,
        documents.OpenApplicationNestedField: NestedField,
    }

    def get_highlight(self, obj):
        if hasattr(obj.meta, 'highlight'):
            return {key.replace('.', '_'): value for key, value in obj.meta.highlight.to_dict().items()}
        return {}
