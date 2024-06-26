import logging
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from api.applications.models import DenialMatchOnApplication
from api.external_data.serializers import DenialEntitySerializer, DenialSerializer
from rest_framework import serializers


from elasticsearch_dsl import connections

from api.documents.libraries import s3_operations
from api.external_data import documents
from api.external_data.helpers import get_denial_entity_enum
from api.external_data.models import DenialEntity

log = logging.getLogger(__name__)


def get_json_content_and_delete(filename):
    json_file = s3_operations.get_object(document_id=filename, s3_key=filename)
    # Let's delete the file
    s3_operations.delete_file(document_id=filename, s3_key=filename)
    return json.load(json_file["Body"])


class Command(BaseCommand):

    required_headers_denial_entity = [
        "name",
        "address",
        "country",
        "spire_entity_id",
    ]

    required_headers_denial = [
        "reference",
        "regime_reg_ref",
        "notifying_government",
        "denial_cle",
        "item_description",
        "end_use",
        "reason_for_refusal",
    ]

    def add_arguments(self, parser):
        parser.add_argument("input_json", type=str, help="Path to the input JSON file")
        parser.add_argument("--rebuild", default=False, action="store_true")

    def rebuild_index(self):
        connection = connections.get_connection()
        connection.indices.delete(index=settings.ELASTICSEARCH_DENIALS_INDEX_ALIAS, ignore=[404])
        documents.DenialEntityDocument.init()

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
        data = get_json_content_and_delete(filename)
        errors = []

        if data:
            # Lets delete all denial records except ones that have been matched
            matched_entity_denial_ids = (
                DenialMatchOnApplication.objects.all().values_list("denial_entity_id", flat=True).distinct()
            )
            DenialEntity.objects.all().exclude(id__in=matched_entity_denial_ids).delete()

        for i, row in enumerate(data, start=1):
            # This is required so we don't reload the same denial entity and load duplicates
            has_fields = bool(row.get("regime_reg_ref") and row.get("name"))
            if has_fields:
                exists = DenialMatchOnApplication.objects.filter(
                    denial_entity__denial__regime_reg_ref=row["regime_reg_ref"], denial_entity__name=row["name"]
                ).exists()
                if exists:
                    continue

            denial_entity_data = {field: row.pop(field, None) for field in self.required_headers_denial_entity}
            denial_data = {field: row.pop(field, None) for field in self.required_headers_denial}
            denial_entity_data["data"] = row
            denial_entity_data["entity_type"] = get_denial_entity_enum(denial_entity_data["data"])

            denial_serializer = DenialSerializer(data=denial_data)

            if denial_serializer.is_valid():
                # Lets first save the denial
                denial = denial_serializer.save()
                log.info(
                    "Saved Denial for row number -> %s",
                    i,
                )
                denial_entity_data.update({"denial": denial.id})
                denial_entity_serializer = DenialEntitySerializer(data=denial_entity_data)
                denial_entity_serializer.is_valid(raise_exception=True)
                # Denial is Save link the denial entity
                denial_entity_serializer.save()
                log.info(
                    "Saved Denial Entity for row number -> %s",
                    i,
                )

            else:
                self.add_bulk_errors(
                    errors=errors,
                    row_number=i + 1,
                    line_errors={**denial_serializer.errors},
                )

        if errors:
            log.exception(
                "Error loading denials -> %s",
                errors,
            )
            raise serializers.ValidationError(errors)
