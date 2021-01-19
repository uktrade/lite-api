from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from api.external_data import models


class DataField(fields.ObjectField):
    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        return instance.data


@registry.register_document
class DenialDocumentType(Document):
    id = fields.KeywordField()
    name = fields.TextField()
    address = fields.TextField()
    reference = fields.KeywordField()
    notifying_government = fields.TextField()
    final_destination = fields.TextField()
    item_list_codes = fields.TextField()
    item_description = fields.TextField()
    consignee_name = fields.TextField()
    end_use = fields.TextField()
    data = DataField()
    is_revoked = fields.BooleanField()

    class Index:
        name = settings.ELASTICSEARCH_DENIALS_INDEX_ALIAS
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "max_ngram_diff": 18,
        }

    class Meta:
        model = models.Denial

    class Django:
        model = models.Denial
