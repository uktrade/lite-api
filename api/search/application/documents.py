from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analysis, InnerDoc
from elasticsearch_dsl.field import Text

from api.applications import models


address_analyzer = analysis.analyzer(
    "address_analyzer", tokenizer="whitespace", filter=["lowercase", "asciifolding", "trim",],
)


part_number_analyzer = analysis.analyzer(
    "part_number_analyzer",
    tokenizer=analysis.tokenizer("part_number_path_hierarchy", "path_hierarchy", delimiter="-"),
    filter=["lowercase", "trim"],
)

reference_code_analyzer = analysis.analyzer(
    "reference_code_analyzer", tokenizer="path_hierarchy", filter=["lowercase", "trim"]
)

descriptive_text_analyzer = analysis.analyzer(
    "descriptive_text_analyzer", tokenizer="classic", filter=["lowercase", "trim", "stemmer"]
)

ngram_filter = analysis.token_filter("ngram_filter", type="ngram", min_gram=2, max_gram=20)

ngram_analyzer = analysis.analyzer(
    "ngram_completion", tokenizer="whitespace", filter=["lowercase", "asciifolding", ngram_filter]
)

whitespace_analyzer = analysis.analyzer(
    "whitespace_analyzer", tokenizer="whitespace", filter=["lowercase", "asciifolding"]
)

lowercase_normalizer = analysis.normalizer("lowercase_normalizer", filter=["lowercase"])


class OpenApplicationNestedField(fields.NestedField):
    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        # get the value from the concrete OpenApplication subclass of the BaseApplication
        try:
            return super().get_value_from_instance(instance.openapplication, field_value_to_ignore)
        except models.OpenApplication.DoesNotExist:
            return []


class Country(InnerDoc):
    name = fields.KeywordField(
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        attr="country.name",
        copy_to="wildcard",
        normalizer=lowercase_normalizer,
    )


class Party(InnerDoc):
    name = fields.TextField(attr="party.name", copy_to="wildcard", analyzer=descriptive_text_analyzer)
    address = fields.TextField(attr="party.address", copy_to="wildcard", analyzer=address_analyzer,)
    country = fields.KeywordField(
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        attr="party.country.name",
        copy_to="wildcard",
    )


class CLCEntryParent(InnerDoc):
    rating = fields.KeywordField(copy_to="wildcard")
    text = fields.TextField(copy_to="wildcard")


class CLCEntry(InnerDoc):
    rating = fields.KeywordField(
        copy_to="wildcard",
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
    )
    text = fields.TextField(copy_to="wildcard", analyzer=descriptive_text_analyzer)
    category = fields.KeywordField(copy_to="wildcard")
    parent = fields.ObjectField(doc_class=CLCEntryParent)


class Parties(InnerDoc):
    name = fields.TextField(attr="party.name", copy_to="wildcard")
    address = fields.TextField(attr="party.address", copy_to="wildcard", analyzer=address_analyzer,)


class Product(InnerDoc):
    quantity = fields.FloatField()
    value = fields.KeywordField()
    unit = fields.KeywordField()
    item_type = fields.KeywordField()
    incorporated = fields.BooleanField(attr="is_good_incorporated")
    description = fields.TextField(attr="good.description", copy_to="wildcard", analyzer=descriptive_text_analyzer,)
    part_number = fields.TextField(
        attr="good.part_number",
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        copy_to="wildcard",
        analyzer=part_number_analyzer,
    )
    organisation = fields.TextField(
        attr="good.organisation.name", copy_to="wildcard", analyzer=descriptive_text_analyzer
    )
    status = fields.KeywordField(attr="good.status")
    comment = fields.TextField(attr="good.comment", copy_to="wildcard", analyzer=descriptive_text_analyzer)
    grading_comment = fields.TextField(
        attr="good.grading_comment", copy_to="wildcard", analyzer=descriptive_text_analyzer
    )
    report_summary = fields.TextField(
        attr="good.report_summary", copy_to="wildcard", analyzer=descriptive_text_analyzer
    )
    is_military_use = fields.TextField(attr="good.is_military_use")
    is_pv_graded = fields.TextField(attr="good.is_pv_graded")
    is_good_controlled = fields.TextField(attr="good.is_good_controlled")
    item_category = fields.TextField(attr="good.item_category")
    control_list_entries = fields.NestedField(attr="good.control_list_entries", doc_class=CLCEntry)


class User(InnerDoc):
    username = fields.KeywordField(attr="username")
    email = fields.KeywordField(attr="email")


@registry.register_document
class ApplicationDocumentType(Document):
    # purposefully not DED field - this is just for collecting other field values for wilcard search
    wildcard = Text(analyzer=ngram_analyzer, search_analyzer=whitespace_analyzer, store=True)
    id = fields.KeywordField(copy_to="wildcard")
    name = fields.TextField(copy_to="wildcard", analyzer=descriptive_text_analyzer)
    reference_code = fields.TextField(
        copy_to="wildcard",
        analyzer=reference_code_analyzer,
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
    )
    case_type = fields.KeywordField(attr="case_type.type")
    organisation = fields.TextField(
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        attr="organisation.name",
        copy_to="wildcard",
        analyzer=descriptive_text_analyzer,
    )
    status = fields.KeywordField(attr="status.status")
    submitted_by = fields.ObjectField(doc_class=User)
    case_officer = fields.ObjectField(doc_class=User)
    goods = fields.NestedField(doc_class=Product)
    parties = fields.NestedField(doc_class=Party)
    destinations = OpenApplicationNestedField(doc_class=Country, attr="application_countries",)

    class Index:
        name = "application-alias"
        settings = {"number_of_shards": 1, "number_of_replicas": 0, "max_ngram_diff": 18}

    class Meta:
        model = models.BaseApplication

    class Django:
        model = models.BaseApplication
