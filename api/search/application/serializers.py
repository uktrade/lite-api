from dateutil import parser
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from api.search.application import documents


class ApplicationDocumentSerializer(DocumentSerializer):
    highlight = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    created = serializers.SerializerMethodField()
    updated = serializers.SerializerMethodField()
    index = serializers.SerializerMethodField()

    class Meta:
        document = documents.ApplicationDocumentType
        fields = (
            "id",
            "queues",
            "name",
            "reference_code",
            "organisation",
            "status",
            "submitted_by",
            "created",
            "updated",
            "case_officer",
            "goods",
            "parties",
            "highlight",
        )
        extra_kwargs = {
            "name": {"required": False},
            "queues": {"required": False},
            "submitted_by": {"required": False},
            "case_officer": {"required": False},
            "created": {"required": False},
            "updated": {"required": False},
        }

    def _get_default_field_kwargs(self, model, field_name, field_type):
        kwargs = super()._get_default_field_kwargs(model, field_name, field_type)
        if field_name in self.Meta.extra_kwargs:
            kwargs.update(self.Meta.extra_kwargs[field_name])
        return kwargs

    def get_highlight(self, obj):
        if hasattr(obj.meta, "highlight"):
            return obj.meta.highlight.to_dict()
        return {}

    def get_score(self, obj):
        return obj.meta.score

    def get_index(self, obj):
        return "spire" if "spire" in obj.meta.index else "lite"

    def get_created(self, obj):
        created = parser.parse(obj.created)
        return created.astimezone().strftime("%H:%M %d %B %Y")

    def get_updated(self, obj):
        updated = parser.parse(obj.updated)
        return updated.astimezone().strftime("%H:%M %d %B %Y")
