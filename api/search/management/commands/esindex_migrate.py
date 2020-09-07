from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections

from api.api.cases.models import Case
from api.search.case import documents


ALIAS = settings.ELASTICSEARCH_CASES_INDEX_ALIAS if settings.LITE_API_ENABLE_ES else ""
PREFIX = "cases-"
PATTERN = f"{PREFIX}*"


class Command(BaseCommand):
    new_index_name = None

    def __init__(self, *args, **kwargs):
        if settings.LITE_API_ENABLE_ES:
            unique_id = get_random_string(length=32).lower()
            self.new_index_name = f"{PREFIX}{unique_id}"
            self.client = connections.get_connection()
        super().__init__(*args, **kwargs)

    def create_index_template(self):
        index_template = documents.CaseDocumentType._index.as_template(ALIAS, PATTERN)
        index_template.save()

    def populate_new_indices(self):
        cases = Case.objects.all()

        data = []
        for case in cases:
            case_document = documents.case_model_to_document(case=case, index_name=self.new_index_name)
            data.append(case_document.to_dict(True))
        bulk(self.client, data)

    def update_aliases(self):
        current_indices = [index for index in self.client.indices.get(PATTERN).keys() if index != self.new_index_name]
        actions = [
            {"remove": {"alias": ALIAS, "index": PATTERN}},
            {"add": {"alias": ALIAS, "index": self.new_index_name}},
        ]

        self.client.indices.update_aliases(body={"actions": actions})

        for index in current_indices:
            self.client.indices.delete(index=index, ignore=[404])

    def handle(self, *args, **options):
        if not settings.LITE_API_ENABLE_ES:
            self.stdout.write(
                self.style.ERROR(f"Elasticsearch indexing is currently disabled, please enable to continue")
            )
            return

        self.create_index_template()
        self.client.indices.create(self.new_index_name)
        self.populate_new_indices()
        self.update_aliases()

        self.stdout.write(self.style.SUCCESS(f"Elasticsearch index migrated, new index name: {self.new_index_name}"))
