import csv
import io
import logging

from django.db import transaction

from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from api.external_data import documents, models
from api.external_data.helpers import get_denial_entity_type
from api.flags.enums import SystemFlags


class DenialEntitySerializer(serializers.ModelSerializer):
    entity_type = serializers.SerializerMethodField()

    class Meta:
        model = models.DenialEntity
        fields = (
            "id",
            "created_by",
            "name",
            "address",
            "reference",
            "regime_reg_ref",
            "notifying_government",
            "country",
            "item_list_codes",
            "item_description",
            "consignee_name",
            "end_use",
            "data",
            "is_revoked",
            "is_revoked_comment",
            "entity_type",
            "reason_for_refusal",
            "spire_entity_id",
        )
        extra_kwargs = {
            "is_revoked": {"required": False},
            "is_revoked_comment": {"required": False},
            "reason_for_refusal": {"required": False},
        }

    def validate(self, data):
        validated_data = super().validate(data)
        if validated_data.get("is_revoked") and not validated_data.get("is_revoked_comment"):
            raise serializers.ValidationError({"is_revoked_comment": "This field is required"})
        return validated_data

    def get_entity_type(self, obj):
        return get_denial_entity_type(obj.data)


class DenialFromCSVFileSerializer(serializers.Serializer):

    csv_file = serializers.CharField()

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

    @transaction.atomic
    def validate_csv_file(self, value):
        csv_file = io.StringIO(value)
        reader = csv.DictReader(csv_file)

        # Check headers exist
        if reader.fieldnames is None:
            raise serializers.ValidationError("CSV file is empty or headers are missing")

        # Check if required headers are present
        if not (set(self.required_headers)).issubset(set(reader.fieldnames)):
            raise serializers.ValidationError("Missing required headers in CSV file")

        errors = []
        for i, row in enumerate(reader, start=1):
            data = {
                **{field: row.get(field, None) for field in self.required_headers},
                "created_by": self.context["request"].user,
            }
            # Create a serializer instance to validate data
            serializer = DenialEntitySerializer(data=data)
            if serializer.is_valid():
                lookup_fields = {
                    "reference": row.get("reference"),
                    "regime_reg_ref": row.get("regime_reg_ref"),
                    "name": row.get("name"),
                    "address": row.get("address"),
                }
                # Try to update an existing record or create a new one
                obj, created = models.DenialEntity.objects.update_or_create(defaults=serializer.validated_data, **lookup_fields)  # type: ignore

                if created:
                    logging.info(f"Created new record at row {i}")

                if not created:
                    logging.info(
                        f"Updated existing record at row {i} based on reference, regime_reg_ref, name, address"
                    )
            else:
                self.add_bulk_errors(errors, i, serializer.errors)

        if errors:
            raise serializers.ValidationError(errors)

        return csv_file

    @staticmethod
    def add_bulk_errors(errors, row_number, line_errors):
        for key, values in line_errors.items():
            errors.append(f"[Row {row_number}] {key}: {','.join(values)}")


class DenialSearchSerializer(DocumentSerializer):
    entity_type = serializers.SerializerMethodField()

    class Meta:
        document = documents.DenialDocumentType
        fields = (
            "id",
            "address",
            "country",
            "end_use",
            "item_description",
            "item_list_codes",
            "name",
            "notifying_government",
            "reference",
            "regime_reg_ref",
        )

    def get_entity_type(self, obj):
        return get_denial_entity_type(obj.data.to_dict())


class SanctionMatchSerializer(serializers.ModelSerializer):
    MATCH_NAME_MAPPING = {
        SystemFlags.SANCTION_UN_SC_MATCH: "UN SC",
        SystemFlags.SANCTION_OFSI_MATCH: "OFSI",
        SystemFlags.SANCTION_UK_MATCH: "UK",
    }

    list_name = serializers.SerializerMethodField()

    class Meta:
        model = models.SanctionMatch
        fields = (
            "id",
            "name",
            "list_name",
            "elasticsearch_reference",
            "is_revoked",
            "is_revoked_comment",
        )

    def validate(self, data):
        validated_data = super().validate(data)
        if validated_data.get("is_removed") and not validated_data.get("is_removed_comment"):
            raise serializers.ValidationError({"is_removed_comment": "This field is required"})
        return validated_data

    def get_list_name(self, obj):
        return self.MATCH_NAME_MAPPING[obj.flag_uuid]
