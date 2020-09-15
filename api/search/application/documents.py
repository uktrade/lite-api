from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analysis, InnerDoc
from elasticsearch_dsl.field import Text

from django.db.models import Prefetch

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

email_analyzer = analysis.analyzer(
    "email_analyzer",
    type="custom",
    tokenizer=analysis.tokenizer(
        "case_officer_email", "pattern", pattern="([a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+\\.[a-zA-Z]{2,})", group=1,
    ),
    filter=["lowercase"],
)


class Country(InnerDoc):
    name = fields.KeywordField(
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        attr="country.name",
        normalizer=lowercase_normalizer,
    )


class Party(InnerDoc):
    name = fields.TextField(attr="party.name", copy_to="wildcard", analyzer=descriptive_text_analyzer)
    address = fields.TextField(attr="party.address", copy_to="wildcard", analyzer=address_analyzer,)
    type = fields.KeywordField(
        attr="party.type",
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
    )
    country = fields.KeywordField(
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        attr="party.country.name",
    )


class CLCEntryParent(InnerDoc):
    rating = fields.KeywordField()
    text = fields.TextField()


class CLCEntry(InnerDoc):
    rating = fields.KeywordField(
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        copy_to="wildcard",
    )
    text = fields.TextField(copy_to="wildcard", analyzer=descriptive_text_analyzer)
    category = fields.KeywordField(
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
    )
    parent = fields.ObjectField(doc_class=CLCEntryParent)


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
        analyzer=part_number_analyzer,
        copy_to="wildcard",
    )
    organisation = fields.TextField(attr="good.organisation.name", analyzer=descriptive_text_analyzer)
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
    username = fields.TextField(
        attr="baseuser_ptr.username",
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        analyzer=descriptive_text_analyzer,
        copy_to="wildcard",
    )
    email = fields.TextField(
        attr="baseuser_ptr.email",
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        analyzer=email_analyzer,
        copy_to="wildcard",
    )


class Queue(InnerDoc):
    id = fields.KeywordField()
    name = fields.TextField(
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        analyzer=descriptive_text_analyzer,
        copy_to="wildcard",
    )
    team = fields.TextField(
        attr="team.name",
        copy_to="wildcard",
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
        analyzer=descriptive_text_analyzer,
    )


@registry.register_document
class ApplicationDocumentType(Document):
    # purposefully not DED field - this is just for collecting other field values for wilcard search
    wildcard = Text(analyzer=ngram_analyzer, search_analyzer=whitespace_analyzer, store=True)
    id = fields.KeywordField()
    queues = fields.NestedField(doc_class=Queue)
    name = fields.TextField(copy_to="wildcard", analyzer=descriptive_text_analyzer)
    reference_code = fields.TextField(
        copy_to="wildcard",
        analyzer=reference_code_analyzer,
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
    )
    organisation = fields.TextField(
        copy_to="wildcard",
        attr="organisation.name",
        analyzer=descriptive_text_analyzer,
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
    )
    status = fields.KeywordField(
        attr="status.status",
        fields={"raw": fields.KeywordField(normalizer=lowercase_normalizer), "suggest": fields.CompletionField(),},
    )
    submitted_by = fields.ObjectField(doc_class=User)
    case_officer = fields.NestedField(doc_class=User)
    goods = fields.NestedField(doc_class=Product)
    parties = fields.NestedField(doc_class=Party)

    created = fields.DateField(attr="created_at")
    updated = fields.DateField(attr="updated_at")

    class Index:
        name = "application-alias"
        settings = {"number_of_shards": 1, "number_of_replicas": 0, "max_ngram_diff": 18}

    class Meta:
        model = models.BaseApplication

    class Django:
        model = models.BaseApplication

    def get_indexing_queryset(self):
        # hack to make `parties` use the prefetch cache. party manager .all() calls .exclude, which clears cache,
        # so work around that here: read from the instance's prefetched_parties attr, which was set in prefetch
        # looks small, but is a huge performance improvement. Helps take db reads down to 7 in total.
        self._fields["parties"]._path = ["prefetched_parties"]

        return (
            self.get_queryset()
            .select_related("organisation")
            .select_related("submitted_by__baseuser_ptr")
            .select_related("case_officer__baseuser_ptr")
            .select_related("status")
            .prefetch_related("queues")
            .prefetch_related("queues__team")
            .prefetch_related(
                Prefetch(
                    "goods",
                    queryset=(
                        models.GoodOnApplication.objects.all()
                        .select_related("good")
                        .select_related("good__organisation")
                        .prefetch_related("good__control_list_entries")
                        .prefetch_related("good__control_list_entries__parent")
                    ),
                )
            )
            .prefetch_related(
                Prefetch(
                    "parties",
                    to_attr="prefetched_parties",
                    queryset=(
                        models.PartyOnApplication.objects.all()
                        .select_related("party")
                        .select_related("party__country")
                        .select_related("party__organisation")
                    ),
                )
            )
        )

    def get_queryset(self):
        return super().get_queryset().exclude(status__status="draft")
