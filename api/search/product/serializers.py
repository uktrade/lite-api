from datetime import datetime
from dateutil import parser
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from api.applications.models import GoodOnApplication
from api.gov_users.serializers import GovUserSimpleSerializer
from api.search.product import documents
from api.search import models


class ProductDocumentSerializer(DocumentSerializer):
    name = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    assessed_by_full_name = serializers.SerializerMethodField()
    highlight = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    index = serializers.SerializerMethodField()
    inner_hits = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        document = documents.ProductDocumentType
        fields = (
            "id",
            "description",
            "control_list_entries",
            "ratings",
            "highlight",
            "destination",
            "organisation",
            "end_use",
            "canonical_name",
            "application",
            "date",
            "assessment_note",
            "report_summary",
            "part_number",
            "regime_entries",
            "regimes",
            "queues",
            "assessed_by",
            "assessment_date",
            "consignee_country",
            "end_user_country",
            "ultimate_end_user_country",
        )
        extra_kwargs = {
            "name": {"required": False, "allow_null": True},
            "canonical_name": {"required": False},
            "id": {"required": False},
            "regime_entries": {"required": False},
            "queues": {"required": False},
        }

    def _get_default_field_kwargs(self, model, field_name, field_type):
        kwargs = super()._get_default_field_kwargs(model, field_name, field_type)
        if field_name in self.Meta.extra_kwargs:
            kwargs.update(self.Meta.extra_kwargs[field_name])
        return kwargs

    def get_name(self, obj):
        return obj.instance.name

    def get_quantity(self, obj):
        return obj.instance.quantity

    def get_value(self, obj):
        return obj.instance.value

    def get_assessed_by_full_name(self, obj):
        return obj.instance.assessed_by.full_name if obj.instance.assessed_by else ""

    def get_highlight(self, obj):
        if hasattr(obj.meta, "highlight"):
            return obj.meta.highlight.to_dict()
        return {}

    def get_score(self, obj):
        if hasattr(obj.meta, "score"):
            return obj.meta.score

    def get_index(self, obj):
        return self.get_index_name(obj.meta.index)

    def get_date(self, obj):
        if hasattr(obj, "date"):
            return self.format_date(obj.date)

    def get_additional_fields_data(self, inner_hits):
        additional_fields_data = {}
        instance_ids = [item["_id"] for item in inner_hits["hits"]["hits"]]
        for instance in GoodOnApplication.objects.filter(id__in=instance_ids):
            key = str(instance.id)
            additional_fields_data[key] = {
                "quantity": instance.quantity,
                "value": instance.value,
                "assessed_by_full_name": instance.assessed_by.full_name if instance.assessed_by else "",
            }

        return additional_fields_data

    def get_inner_hits(self, obj):
        if hasattr(obj.meta, "inner_hits"):
            inner_hits = obj.meta.inner_hits.related.to_dict()
            additional_fields_data = self.get_additional_fields_data(inner_hits)
            return {
                "total": inner_hits["hits"]["total"]["value"],
                "hits": [
                    {
                        **item["_source"],
                        **additional_fields_data[item["_id"]],
                        "date": self.format_date(item["_source"]["date"]),
                        "highlight": item.get("highlight", {}),
                        "index": self.get_index_name(item["_index"]),
                    }
                    for item in inner_hits["hits"]["hits"]
                ],
            }
        return {}

    @staticmethod
    def get_index_name(name):
        return "spire" if "spire" in name else "lite"

    @staticmethod
    def format_date(date):
        if not date:
            return date
        if isinstance(date, datetime):
            value = date
        else:
            value = parser.parse(date)
        return value.astimezone().strftime("%d %B %Y")
