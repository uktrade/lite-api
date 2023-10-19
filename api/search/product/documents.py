from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analysis, InnerDoc
from elasticsearch_dsl.field import Text

from api.applications import models


address_analyzer = analysis.analyzer(
    "address_analyzer",
    tokenizer="whitespace",
    filter=[
        "lowercase",
        "asciifolding",
        "trim",
    ],
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

email_analyzer = analysis.analyzer(
    "email_analyzer",
    type="custom",
    tokenizer=analysis.tokenizer(
        "case_officer_email",
        "pattern",
        pattern="([a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+\\.[a-zA-Z]{2,})",
        group=1,
    ),
    filter=["lowercase"],
)


class Rating(InnerDoc):
    rating = fields.KeywordField(
        fields={
            "raw": fields.KeywordField(normalizer=lowercase_normalizer),
            "suggest": fields.CompletionField(),
        },
        copy_to="wildcard",
    )
    text = fields.TextField(
        copy_to="wildcard",
        analyzer=descriptive_text_analyzer,
    )


class ApplicationOnProduct(InnerDoc):
    id = fields.KeywordField()
    reference_code = fields.KeywordField()


class Queue(InnerDoc):
    id = fields.KeywordField()
    name = fields.TextField(
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField()},
        analyzer=descriptive_text_analyzer,
        copy_to="wildcard",
    )
    team = fields.TextField(
        attr="team.name",
        copy_to="wildcard",
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField()},
        analyzer=descriptive_text_analyzer,
    )


class ProductDocumentType(Document):
    # purposefully not DED field - this is just for collecting other field values for wilcard search
    wildcard = Text(
        analyzer=ngram_analyzer,
        search_analyzer=whitespace_analyzer,
        store=True,
    )
    # purposefully not DED field - this is just for collecting other field values for grouping purposes in ES
    context = fields.Keyword()

    # used for grouping
    canonical_name = fields.KeywordField(attr="good.name")  # is overwritten in prepare

    # base details. iteration 1
    id = fields.KeywordField()
    description = fields.TextField(
        attr="good.description",
        copy_to="wildcard",
        analyzer=descriptive_text_analyzer,
    )
    control_list_entries = fields.NestedField(attr="good.control_list_entries", doc_class=Rating)
    queues = fields.NestedField(doc_class=Queue, attr="application.queues")

    organisation = fields.TextField(
        copy_to="wildcard",
        attr="good.organisation.name",
        analyzer=descriptive_text_analyzer,
        fields={
            "raw": fields.KeywordField(normalizer=lowercase_normalizer),
            "suggest": fields.CompletionField(),
        },
    )

    name = fields.TextField(attr="good.name", copy_to="wildcard", analyzer=descriptive_text_analyzer)
    # not mapped yet
    destination = fields.KeywordField(
        attr="application.end_user.party.country.name",
        fields={
            "raw": fields.KeywordField(normalizer=lowercase_normalizer),
            "suggest": fields.CompletionField(),
        },
        normalizer=lowercase_normalizer,
    )
    end_use = fields.TextField(attr="application.intended_end_use")
    end_user_type = fields.KeywordField(
        attr="application.end_user.party.sub_type",
        normalizer=lowercase_normalizer,
    )

    organisation = fields.TextField(
        copy_to="wildcard",
        attr="good.organisation.name",
        analyzer=descriptive_text_analyzer,
        fields={
            "raw": fields.KeywordField(normalizer=lowercase_normalizer),
            "suggest": fields.CompletionField(),
        },
    )
    date = fields.DateField(attr="application.submitted_at")

    application = fields.NestedField(doc_class=ApplicationOnProduct)

    rating_comment = fields.TextField(attr="good.comment", copy_to="wildcard", analyzer=descriptive_text_analyzer)

    report_summary = fields.TextField(
        attr="good.report_summary",
        fields={
            "raw": fields.KeywordField(normalizer=lowercase_normalizer),
            "suggest": fields.CompletionField(),
        },
        analyzer=descriptive_text_analyzer,
        copy_to="wildcard",
    )

    part_number = fields.TextField(
        attr="good.part_number",
        fields={
            "raw": fields.KeywordField(normalizer=lowercase_normalizer),
            "suggest": fields.CompletionField(),
        },
        analyzer=part_number_analyzer,
        copy_to="wildcard",
    )

    regime = fields.Keyword()

    class Index:
        name = settings.ELASTICSEARCH_PRODUCT_INDEX_ALIAS
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "max_ngram_diff": 18,
        }

    class Meta:
        model = models.GoodOnApplication

    class Django:
        model = models.GoodOnApplication

    def get_queryset(self):
        return super().get_queryset().exclude(application__status__status="draft")

    def prepare(self, instance):
        data = super().prepare(instance)
        data["context"] = f"{data['destination']}🔥{data['end_use']}🔥{data['end_user_type']}"
        data["canonical_name"] = data["description"]
        return data

    def get_indexing_queryset(self):
        return (
            self.get_queryset()
            .select_related("good")
            .select_related("application")
            .select_related("good__organisation")
            .prefetch_related("application__parties__party__flags")
        )


if settings.LITE_API_ENABLE_ES:
    registry.register_document(ProductDocumentType)
