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
    data = DataField()

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

    def get_indexing_queryset(self):
        return self.get_queryset().exclude(is_revoked=True)


class SanctionDocumentType(Document):

    list_type = fields.Keyword()
    reference = fields.Keyword()
    name = fields.Text()
    data = fields.Object(properties={
        'listed_on': fields.TextField(),
        'individual_date_of_birth': fields.Object(properties={
            'date': fields.TextField(),
        })
    })

    class Index:
        name = settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "max_ngram_diff": 18,
        }
