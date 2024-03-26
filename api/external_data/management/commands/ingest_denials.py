import logging
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from api.external_data.helpers import get_denial_entity_type

from elasticsearch_dsl import connections

from api.documents.libraries import s3_operations
from api.external_data import documents
from api.external_data.models import DenialEntity, NewDenial

log = logging.getLogger(__name__)


def get_json_content_and_delete(filename):
    json_file = s3_operations.get_object(document_id=filename, s3_key=filename)
    # Let's delete the file
    s3_operations.delete_file(document_id=filename, s3_key=filename)
    return json.load(json_file["Body"])


class Command(BaseCommand):

    required_headers = [
        "reference",
        "regime_reg_ref",
        "name",
        "address",
        "notifying_government",
        "country",
        "item_list_codes",
        "item_description",
        "consignee_name",
        "end_use",
        "reason_for_refusal",
        "spire_entity_id",
    ]

    denial_headers = [
        "reference",
        "regime_reg_ref",
        "notifying_government",
        "item_list_codes",
        "item_description",
        "end_use",
        "reason_for_refusal",
    ]
    denial_entity_headers = [
        "name",
        "address",
        "country",
        "type",
    ]

    def add_arguments(self, parser):
        parser.add_argument("input_json", type=str, help="Path to the input JSON file")
        parser.add_argument("--rebuild", default=False, action="store_true")

    def rebuild_index(self):
        connection = connections.get_connection()
        connection.indices.delete(index=settings.ELASTICSEARCH_DENIALS_INDEX_ALIAS, ignore=[404])
        documents.DenialDocumentType.init()

    def handle(self, *args, **options):
        if options["rebuild"]:
            self.rebuild_index()
        self.load_denials(options["input_json"])

    @transaction.atomic
    def load_denials(self, filename):

        data = get_json_content_and_delete(filename)

        for i, row in enumerate(data, start=1):

            try:

                data = {field: row.get(field, None) for field in self.denial_headers}
                row["type"] = get_denial_entity_type(row)

                instance, _ = NewDenial.objects.get_or_create(**data)
                log.info(
                    "Saved Denial row number -> %s",
                    i,
                )

                entity_data = {field: row.get(field, None) for field in self.denial_entity_headers}

                DenialEntity.objects.get_or_create(denial_id=instance, **entity_data)

                log.info(
                    "Saved Denial Entity row number -> %s",
                    i,
                )

            except Exception as ex:
                log.info(
                    "Failed Denial loading at row number -> %s %s",
                    i,
                    ex,
                )
                raise ex
