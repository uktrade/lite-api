import csv
import io

import logging
from django.db import transaction
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from api.external_data import documents, models
from api.external_data.helpers import get_denial_entity_type, get_denial_entity_type_db_representation
from api.flags.enums import SystemFlags
from api.external_data.models import DenialEntity


class EntityTypeSerializerField(serializers.Field):

    def to_representation(self, obj):
        return get_denial_entity_type(obj.data)

    def to_internal_value(self, data):
        return (
            data + "test"
        )  # get_denial_entity_type_db_representation(data)  # this needs to return the entity type db representation


class DenialEntitySerializer(serializers.ModelSerializer):
    entity_type = EntityTypeSerializerField()

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


# TODO: this is for backwards compatibility and should be removed
# once the lite-routing test data has been updated
class DenialFromCSVFileOldSerializer(serializers.Serializer):

    csv_file = serializers.CharField()
    required_headers = [
        "reference",
        "name",
        "address",
        "notifying_government",
        "country",
        "item_list_codes",
        "item_description",
        "consignee_name",
        "end_use",
    ]

    @transaction.atomic
    def validate_csv_file(self, value):
        csv_file = io.StringIO(value)
        dialect = csv.Sniffer().sniff(csv_file.read(1024))
        csv_file.seek(0)
        reader = csv.reader(csv_file, dialect=dialect)
        headers = next(reader, None)
        errors = []
        valid_serializers = []
        for i, row in enumerate(reader, start=1):
            data = dict(zip(headers, row))
            serializer = DenialEntitySerializer(
                data={
                    "data": data,
                    "created_by": self.context["request"].user,
                    **{field: data.pop(field, None) for field in self.required_headers},
                }
            )

            if serializer.is_valid():
                valid_serializers.append(serializer)
            else:
                self.add_bulk_errors(errors=errors, row_number=i + 1, line_errors=serializer.errors)
        if errors:
            raise serializers.ValidationError(errors)
        else:
            # only save if no errors
            for serializer in valid_serializers:
                serializer.save()
        return csv_file

    @staticmethod
    def add_bulk_errors(errors, row_number, line_errors):
        for key, values in line_errors.items():
            errors.append(f"[Row {row_number}] {key}: {','.join(values)}")


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

        # Check if required headers are present
        if not (set(self.required_headers)).issubset(set(reader.fieldnames)):  # type: ignore
            raise serializers.ValidationError("Missing required headers in CSV file")

        logging_counts = {"denial": {"created": 0, "updated": 0}, "denial_entity": {"created": 0, "updated": 0}}
        logging_regime_reg_ref_values = {
            "denial": {"created": [], "updated": []},
            "denial_entity": {"created": [], "updated": []},
        }
        errors = []
        for i, row in enumerate(reader, start=1):
            denial_entity_data = {
                **{field: row[field] for field in self.required_headers},
                "created_by": self.context["request"].user,
            }
            # Create a serializer instance to validate data
            serializer = DenialEntitySerializer(data=denial_entity_data)
            if serializer.is_valid() and isinstance(serializer.validated_data, dict):
                # Try to update an existing Denial record or create a new one
                regime_reg_ref = serializer.validated_data["regime_reg_ref"]
                denial_data = {
                    "reference": serializer.validated_data["reference"],
                    "notifying_government": serializer.validated_data["notifying_government"],
                    "item_list_codes": serializer.validated_data["item_list_codes"],
                    "item_description": serializer.validated_data["item_description"],
                    "end_use": serializer.validated_data["end_use"],
                    "reason_for_refusal": serializer.validated_data["reason_for_refusal"],
                }
                denial, is_denial_created = models.Denial.objects.update_or_create(
                    regime_reg_ref=regime_reg_ref, defaults=denial_data
                )

                if is_denial_created:
                    logging_counts["denial"]["created"] += 1
                    logging_regime_reg_ref_values["denial"]["created"].append(denial.regime_reg_ref)
                else:
                    logging_counts["denial"]["updated"] += 1
                    logging_regime_reg_ref_values["denial"]["updated"].append(denial.regime_reg_ref)

                # We assume that a DenialEntity object already exists if we can
                # match on all of the following fields
                denial_entity_lookup_fields = {
                    "reference": serializer.validated_data["reference"],
                    "regime_reg_ref": regime_reg_ref,
                    "name": serializer.validated_data["name"],
                    "address": serializer.validated_data["address"],
                }
                # Link the validated DenialEntity data with the Denial
                denial_entity, is_denial_entity_created = models.DenialEntity.objects.update_or_create(
                    defaults=serializer.validated_data, denial=denial, **denial_entity_lookup_fields
                )

                if is_denial_entity_created:
                    logging_counts["denial_entity"]["created"] += 1
                    logging_regime_reg_ref_values["denial_entity"]["created"].append(denial_entity.regime_reg_ref)
                else:
                    logging_counts["denial_entity"]["updated"] += 1
                    logging_regime_reg_ref_values["denial_entity"]["updated"].append(denial_entity.regime_reg_ref)
            else:
                self.add_bulk_errors(errors, i, serializer.errors)

        if errors:
            raise serializers.ValidationError(errors)

        if logging_counts["denial"]["created"]:
            logging.info(
                "Created %s Denial records with regime_reg_ref values:\n%s",
                logging_counts["denial"]["created"],
                "\n".join(logging_regime_reg_ref_values["denial"]["created"]),
            )
        if logging_counts["denial"]["updated"]:
            logging.info(
                "Updated %s Denial records with regime_reg_ref values:\n%s",
                logging_counts["denial"]["updated"],
                "\n".join(logging_regime_reg_ref_values["denial"]["updated"]),
            )

        if logging_counts["denial_entity"]["created"]:
            logging.info(
                "Created %s DenialEntity records with regime_reg_ref values:\n%s",
                logging_counts["denial_entity"]["created"],
                "\n".join(logging_regime_reg_ref_values["denial_entity"]["created"]),
            )
        if logging_counts["denial_entity"]["updated"]:
            logging.info(
                "Updated %s DenialEntity records with regime_reg_ref values:\n%s",
                logging_counts["denial_entity"]["updated"],
                "\n".join(logging_regime_reg_ref_values["denial_entity"]["updated"]),
            )

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
