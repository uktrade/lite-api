from dateutil import parser
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from api.search.product import documents


class ProductDocumentSerializer(DocumentSerializer):
    highlight = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    index = serializers.SerializerMethodField()
    inner_hits = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        document = documents.ProductDocumentType
        fields = (
            "id",
            "name",
            "description",
            "control_list_entries",
            "highlight",
            "destination",
            "organisation",
            "end_use",
            "canonical_name",
            "application",
            "date",
            "rating_comment",
            "report_summary",
            "part_number",
        )
        extra_kwargs = {
            "name": {"required": False, "allow_null": True},
            "canonical_name": {"required": False},
            "id": {"required": False},
            "regime": {"required": False},
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
        return self.get_index_name(obj.meta.index)

    def get_date(self, obj):
        if hasattr(obj, "date"):
            self.format_date(obj.date)

    def get_inner_hits(self, obj):
        if hasattr(obj.meta, "inner_hits"):
            inner_hits = obj.meta.inner_hits.related.to_dict()
            return {
                "total": inner_hits["hits"]["total"]["value"],
                "hits": [
                    {
                        **item["_source"],
                        "date": self.format_date(item["_source"]["date"]),
                        "highlight": item.get("highlight", {}),
                        "index": self.get_index_name(item["_index"]),
                    }
                    for item in inner_hits["hits"]["hits"]
                ],
            }
        return []

    @staticmethod
    def get_index_name(name):
        return "spire" if "spire" in name else "lite"

    @staticmethod
    def format_date(date):
        if not date:
            return date
        value = parser.parse(date)
        return value.astimezone().strftime("%Y")
