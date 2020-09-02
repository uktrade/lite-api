from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.fields import (
    BooleanField, FloatField, ListField, ObjectField, TextField, KeywordField, NestedField, Nested
)
from rest_framework.fields import DecimalField

from api.applications.models import BaseApplication

from elasticsearch_dsl import InnerDoc


class Parties(InnerDoc):
    name = TextField(attr='party.name', copy_to='wildcard')
    address = KeywordField(attr='party.address', copy_to='wildcard')


@registry.register_document
class ApplicationDocumentType(Document):
    wildcard = TextField(attr='id')

    id = TextField()
    reference_code = TextField(copy_to='wildcard')
    case_type = TextField(attr="case_type.type")
    organisation = TextField(attr="organisation.name")
    status = TextField(attr="status.status")
    submitted_by = ObjectField(
        properties={
            "username": TextField(attr="username"),
            "email": TextField(attr="email"),
        }
    )
    case_officer= ObjectField(
        properties={
            "username": TextField(attr="username"),
            "email": TextField(attr="email"),
        }
    )
    products = NestedField(
        attr="goods",
        properties={
            "quantity": FloatField(),
            "value": FloatField(),
            "unit": TextField(),
            "item_type": TextField(),
            "incorporated": BooleanField(attr="is_good_incorporated"),
            "good": ObjectField(
                properties={
                    "id": TextField(),
                    "description": TextField(copy_to='wildcard'),
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
        }
    )
    parties = NestedField(doc_class=Parties)

    class Index:
        name = "application-alias"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Meta:
        model = BaseApplication

    class Django:
        model = BaseApplication
