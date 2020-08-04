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
        name = "cases-alias"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Meta:
        model = Case

    class Django:
        model = Case


def case_model_to_document(case, index_name):
    document = CaseDocumentType(
        meta={"id": case.pk, "_index": index_name},
        id=case.pk,
        reference_code=case.reference_code,
        organisation=case.organisation.id,
    )

    return document
