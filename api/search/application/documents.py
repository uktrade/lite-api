from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.fields import (
    BooleanField,
    FloatField,
    ObjectField,
    TextField,
    KeywordField,
    NestedField,
    CompletionField
)

from api.applications import models

from elasticsearch_dsl import analysis, InnerDoc


address_analyzer = analysis.analyzer(
    'address_analyzer',
    tokenizer='whitespace',
    filter=['lowercase', 'asciifolding', 'trim'],
)


part_number_analyzer = analysis.analyzer(
    'part_number_analyzer',
    tokenizer=analysis.tokenizer('part_number_path_hierarchy', 'path_hierarchy', delimiter='-'),
    filter=['lowercase', 'trim'],
)

reference_code_analyzer = analysis.analyzer(
    'reference_code_analyzer',
    tokenizer='path_hierarchy',
    filter=['lowercase', 'trim']
)

descriptive_text_analyzer = analysis.analyzer(
    'descriptive_text_analyzer',
    tokenizer='edge_ngram',
    filter=['lowercase', 'trim']
)

lowercase_normalizer = analysis.normalizer('lowercase_normalizer', filter=['lowercase'])


class OpenApplicationNestedField(NestedField):
    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        # get the value from the concrete OpenApplication subclass of the BaseApplication
        try:
            return super().get_value_from_instance(instance.openapplication, field_value_to_ignore)
        except models.OpenApplication.DoesNotExist:
            return []


class Country(InnerDoc):
    name = KeywordField(attr='country.name', copy_to="wildcard", normalizer=lowercase_normalizer)


class Party(InnerDoc):
    name = TextField(attr="party.name", copy_to="wildcard", analyzer=descriptive_text_analyzer)
    address = TextField(
        attr="party.address",
        copy_to="wildcard",
        analyzer=address_analyzer,
    )
    country = KeywordField(attr='party.country.name', copy_to="wildcard", normalizer=lowercase_normalizer)


class CLCEntry(InnerDoc):
    rating = KeywordField(copy_to="wildcard", normalizer=lowercase_normalizer)
    text = TextField(copy_to="wildcard", analyzer=descriptive_text_analyzer)
    category = KeywordField(copy_to="wildcard")
    parent = TextField(attr="parent.text", analyzer=descriptive_text_analyzer)


class Good(InnerDoc):
    id = KeywordField(copy_to="wildcard")
    description = TextField(copy_to="wildcard", analyzer=descriptive_text_analyzer)
    part_number = TextField(copy_to="wildcard", analyzer=part_number_analyzer)
    organisation = TextField(attr="organisation.name", analyzer=descriptive_text_analyzer)
    status = KeywordField()
    comment = TextField(copy_to="wildcard", analyzer=descriptive_text_analyzer)
    grading_comment = TextField(analyzer=descriptive_text_analyzer)
    report_summary = TextField(copy_to="wildcard", analyzer=descriptive_text_analyzer)
    is_military_use = TextField()
    is_pv_graded = TextField()
    is_good_controlled = TextField()
    item_category = TextField()
    control_list_entries = NestedField(doc_class=CLCEntry)


class Product(InnerDoc):
    quantity = FloatField()
    value = KeywordField()
    unit = KeywordField()
    item_type = KeywordField()
    incorporated = BooleanField(attr="is_good_incorporated")
    good = NestedField(doc_class=Good)


class User(InnerDoc):
    username = KeywordField(attr="username")
    email = KeywordField(attr="email")


@registry.register_document
class ApplicationDocumentType(Document):
    wildcard = TextField(
        attr="id",
        fields={
            'raw': TextField(),
            'suggest': CompletionField(),
        }
    )

    id = KeywordField(copy_to="wildcard")
    name = TextField(copy_to="wildcard", analyzer=descriptive_text_analyzer)
    reference_code = TextField(copy_to="wildcard", analyzer=reference_code_analyzer)
    case_type = KeywordField(attr="case_type.type")
    organisation = TextField(attr="organisation.name", copy_to="wildcard", analyzer=descriptive_text_analyzer)
    status = KeywordField(attr="status.status")
    submitted_by = ObjectField(doc_class=User)
    case_officer = ObjectField(doc_class=User)
    goods = NestedField(doc_class=Product)
    parties = NestedField(doc_class=Party)
    destinations = OpenApplicationNestedField(doc_class=Country, attr='application_countries',)

    class Index:
        name = "application-alias"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Meta:
        model = models.BaseApplication

    class Django:
        model = models.BaseApplication
