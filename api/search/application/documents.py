from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.fields import (
    BooleanField,
    FloatField,
    ObjectField,
    TextField,
    KeywordField,
    NestedField,
)

from api.applications.models import BaseApplication

from elasticsearch_dsl import analysis, InnerDoc


address_analyzer = analysis.analyzer(
    "address_analyzer", tokenizer="whitespace", filter=["lowercase", "asciifolding", "trim",],
)


part_number_analyzer = analysis.analyzer(
    "part_number_analyzer",
    tokenizer=analysis.tokenizer("part_number_path_hierarchy", "path_hierarchy", delimiter="-"),
    filter=["lowercase", "trim",],
)


class Parties(InnerDoc):
    name = TextField(attr="party.name", copy_to="wildcard")
    address = TextField(attr="party.address", copy_to="wildcard", analyzer=address_analyzer,)


class CLCEntry(InnerDoc):
    rating = KeywordField(copy_to="wildcard")
    text = TextField(copy_to="wildcard")
    category = TextField(copy_to="wildcard")
    parent = ObjectField(
        properties={
            "rating": KeywordField(attr="rating", copy_to="wildcard"),
            "text": TextField(attr="text", copy_to="wildcard"),
        }
    )


class Good(InnerDoc):
    id = TextField()
    description = TextField(copy_to="wildcard")
    part_number = TextField(copy_to="wildcard", analyzer=part_number_analyzer)
    organisation = TextField(attr="organisation.name")
    status = KeywordField()
    comment = TextField(copy_to="wildcard")
    grading_comment = TextField()
    report_summary = TextField(copy_to="wildcard")
    is_military_use = TextField()
    is_pv_graded = TextField()
    is_good_controlled = TextField()
    item_category = TextField()
    control_list_entries = NestedField(doc_class=CLCEntry)


class Products(InnerDoc):
    quantity = FloatField()
    value = KeywordField()
    unit = KeywordField()
    item_type = KeywordField()
    incorporated = BooleanField(attr="is_good_incorporated")
    good = NestedField(doc_class=Good)


@registry.register_document
class ApplicationDocumentType(Document):
    wildcard = TextField(attr="id")

    id = TextField()
    reference_code = TextField(copy_to="wildcard")
    case_type = TextField(attr="case_type.type")
    organisation = TextField(attr="organisation.name", copy_to="wildcard")
    status = TextField(attr="status.status")
    submitted_by = ObjectField(properties={"username": TextField(attr="username"), "email": TextField(attr="email"),})
    case_officer = ObjectField(properties={"username": TextField(attr="username"), "email": TextField(attr="email"),})
    goods = NestedField(doc_class=Products)
    parties = NestedField(doc_class=Parties)

    class Index:
        name = "application-alias"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Meta:
        model = BaseApplication

    class Django:
        model = BaseApplication
