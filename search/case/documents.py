from organisations.models import Organisation
from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.fields import ListField, TextField

from cases.models import Case


@registry.register_document
class CaseDocumentType(Document):
    id = TextField()
    reference_code = TextField()
    organisation = TextField(attr="organisation.name")

    class Index:
        name = 'cases'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Meta:
        model = Case


    class Django:
        model = Case
