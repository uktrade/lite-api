from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.fields import TextField

from api.cases.models import Case


@registry.register_document
class CaseDocumentType(Document):
    id = TextField()
    reference_code = TextField()
    case_type = TextField(attr="case_type.type")
    organisation = TextField(attr="organisation.name")
    status = TextField(attr="status.status")

    class Index:
        name = "cases-alias"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Meta:
        model = Case

    class Django:
        model = Case

    def get_indexing_queryset(self):
        return self.get_queryset().select_related("case_type").select_related("organisation").select_related("status")


def case_model_to_document(case, index_name):
    document = CaseDocumentType(
        meta={"id": case.pk, "_index": index_name},
        id=case.pk,
        reference_code=case.reference_code,
        case_type=case.case_type.type,
        organisation=case.organisation.name,
        status=case.status.status,
    )

    return document
