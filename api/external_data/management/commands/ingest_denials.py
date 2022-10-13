import logging
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from rest_framework import serializers

from elasticsearch_dsl import connections

from api.documents.libraries import s3_operations
from api.external_data import documents
from api.external_data.serializers import DenialSerializer

log = logging.getLogger(__name__)


def get_json_content(filename):
    json_file = s3_operations.get_object(document_id=filename, s3_key=filename)
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
    ]

    def add_arguments(self, parser):
        parser.add_argument("input_json", type=str, help="Path to the input JSON file")
        parser.add_argument("--rebuild", default=False, action="store_true")

    def rebuild_index(self):
        connection = connections.get_connection()
        connection.indices.delete(index=settings.ELASTICSEARCH_DENIALS_INDEX_ALIAS, ignore=[404])
        documents.DenialDocumentType.init()

    @staticmethod
    def add_bulk_errors(errors, row_number, line_errors):
        for key, values in line_errors.items():
            errors.append(f"[Row {row_number}] {key}: {','.join(values)}")

    def handle(self, *args, **options):
        if options["rebuild"]:
            self.rebuild_index()
        self.load_denials(options["input_json"])

    @transaction.atomic
    def load_denials(self, filename):
        data = get_json_content(filename)
        errors = []
        for i, row in enumerate(data, start=1):
            serializer = DenialSerializer(
                data={
                    "data": row,
                    **{field: row.pop(field, None) for field in self.required_headers},
                }
            )
            if i == 100:
                break
            if serializer.is_valid():
                serializer.save()
                log.info(
                    "Saved row number -> %s",
                    i,
                )
            else:
                self.add_bulk_errors(errors=errors, row_number=i + 1, line_errors=serializer.errors)

        if errors:
            log.exception(
                "Error loading denials -> %s",
                errors,
            )
            raise serializers.ValidationError(errors)
