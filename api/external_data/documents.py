from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analysis

from api.external_data import models
from api.search.application.documents import lowercase_normalizer


class DataField(fields.ObjectField):
    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        return instance.data


custom_ascii_folding_filter = analysis.token_filter(
    "custom_ascii_folding_filter", type="asciifolding", preserve_original=True
)


name_analyzer = analysis.analyzer(
    "name_analyzer",
    tokenizer="standard",
    filter=["lowercase", "trim", custom_ascii_folding_filter],
)

postcode_filter = analysis.char_filter(
    "postcode_filter",
    type="pattern_replace",
    pattern="\\s+",
    replacement=" ",
)

ngram_filter = analysis.token_filter("ngram_filter", type="ngram", min_gram=2, max_gram=10)

address_stop_words_filter = analysis.token_filter(
    "address_stop_words_filter",
    type="stop",
    stopwords=[
        "avenue",
        "boulevard",
        "Box",
        "court",
        "drive",
        "lane",
        "loop",
        "po",
        "pob",
        "road",
        "route",
        "street",
        "way",
        "suite",
    ],
    ignore_case=True,
)

address_analyzer = analysis.analyzer(
    "address_analyzer",
    tokenizer="whitespace",
    filter=["lowercase", "asciifolding", "trim", address_stop_words_filter, ngram_filter],
)

postcode_normalizer = analysis.normalizer(
    "postcode_normalizer",
    type="custom",
    char_filter=[postcode_filter],
    filter=["lowercase", "asciifolding"],
)


class DenialDocumentType(Document):
    id = fields.KeywordField()
    name = fields.TextField()
    address = fields.Text(analyzer=address_analyzer)
    reference = fields.KeywordField()
    regime_reg_ref = fields.KeywordField()
    notifying_government = fields.TextField()
    country = fields.TextField(
        fields={
            "raw": fields.KeywordField(normalizer=lowercase_normalizer),
        },
    )
    item_list_codes = fields.TextField()
    item_description = fields.TextField()
    consignee_name = fields.TextField()
    end_use = fields.TextField()
    data = DataField()
    is_revoked = fields.BooleanField()

    class Index:
        name = settings.ELASTICSEARCH_DENIALS_INDEX_ALIAS
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "max_ngram_diff": 18,
        }

    class Meta:
        model = models.Denial

    class Django:
        model = models.Denial


class SanctionDocumentType(Document):

    flag_uuid = fields.Keyword()
    reference = fields.Keyword()
    name = fields.Text(analyzer=name_analyzer)
    address = fields.Text(analyzer=address_analyzer)
    postcode = fields.Keyword(normalizer=postcode_normalizer)

    data = fields.Object(
        properties={
            "listed_on": fields.TextField(),
            "individual_date_of_birth": fields.Object(
                properties={
                    "date": fields.TextField(),
                }
            ),
            "title": fields.TextField(),
            "Last Updated": fields.TextField(),
            "Date Designated": fields.TextField(),
        }
    )

    class Index:
        name = settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "max_ngram_diff": 18,
        }


if settings.LITE_API_ENABLE_ES:
    registry.register_document(DenialDocumentType)
