from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.fields import BooleanField, FloatField, ListField, ObjectField, TextField
from rest_framework.fields import DecimalField

from api.applications.models import GoodOnApplication


@registry.register_document
class GoodOnApplicationDocumentType(Document):
    id = TextField()
    quantity = FloatField()
    value = DecimalField(max_digits=15, decimal_places=2)
    unit = TextField()
    item_type = TextField()
    incorporated = BooleanField(attr="is_good_incorporated")
    good = ObjectField(
        properties={
            "id": TextField(),
            "description": TextField(),
            "part_number": TextField(),
            "organisation": TextField(attr="organisation.name"),
            "status": TextField(),
            "comment": TextField(),
            "grading_comment": TextField(),
            "report_summary": TextField(),
            "is_military_use": TextField(),
            "is_pv_graded": TextField(),
            "is_good_controlled": TextField(),
            "item_category": TextField(),
            "clc_entries": ListField(
                ObjectField(
                    attr="control_list_entries",
                    properties={
                        "rating": TextField(),
                        "text": TextField(),
                        "category": TextField(),
                        "parent": TextField(attr="parent.text"),
                    },
                )
            ),
        }
    )
    application = ObjectField(
        properties={
            "id": TextField(),
            "reference_code": TextField(),
            "case_type": TextField(attr="case_type.type"),
            "organisation": TextField(attr="organisation.name"),
            "status": TextField(attr="status.status"),
            "submitted_by": ObjectField(
                properties={
                    "username": TextField(attr="username"),
                    "email": TextField(attr="email"),
                }
            ),
            "case_officer": ObjectField(
                properties={
                    "username": TextField(attr="username"),
                    "email": TextField(attr="email"),
                }
            ),
        }
    )

    class Index:
        name = "goa-alias"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Meta:
        model = GoodOnApplication

    class Django:
        model = GoodOnApplication
