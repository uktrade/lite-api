import csv
import io

import logging
from django.db import transaction
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from api.external_data import documents, models

from api.flags.enums import SystemFlags
from api.core.serializers import KeyValueChoiceField
from api.external_data.helpers import get_denial_entity_type
from django.utils.html import escape


class DenialSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = models.Denial
        fields = (
            "id",
            "created_by_user",
            "regime_reg_ref",
            "notifying_government",
            "denial_cle",
            "item_description",
            "end_use",
            "is_revoked",
            "is_revoked_comment",
            "reason_for_refusal",
            "reference",
        )
        extra_kwargs = {
            "is_revoked": {"required": False},
            "is_revoked_comment": {"required": False},
            "reason_for_refusal": {"required": False},
        }


class DenialEntitySerializer(serializers.ModelSerializer):
    entity_type = KeyValueChoiceField(choices=models.DenialEntityType.choices, required=False)
    regime_reg_ref = serializers.CharField(source="denial.regime_reg_ref", required=False)
    denial_cle = serializers.CharField(source="denial.denial_cle", required=False)
    notifying_government = serializers.CharField(source="denial.notifying_government", required=False)
    item_description = serializers.CharField(source="denial.item_description", required=False)
    end_use = serializers.CharField(source="denial.end_use", required=False)
    is_revoked = serializers.BooleanField(source="denial.is_revoked", required=False)
    is_revoked_comment = serializers.CharField(source="denial.is_revoked_comment", required=False)
    reason_for_refusal = serializers.CharField(source="denial.reason_for_refusal", required=False)
    reference = serializers.CharField(source="denial.reference", required=False, allow_blank=True)

    class Meta:
        model = models.DenialEntity
        fields = (
            "id",
            "created_by",
            "name",
            "address",
            "regime_reg_ref",
            "notifying_government",
            "country",
            "denial_cle",
            "item_description",
            "end_use",
            "is_revoked",
            "is_revoked_comment",
            "reason_for_refusal",
            "entity_type",
            "reference",
            "denial",
        )

        extra_kwargs = {
            "is_revoked": {"required": False},
            "is_revoked_comment": {"required": False},
            "reason_for_refusal": {"required": False},
        }

    def validate(self, data):
        # Currently a denial can be a new value being updated or an existing denial object being revoked from the UI
        validated_data = super().validate(data)
        denial = validated_data.get("denial")
        is_dict_update = isinstance(denial, dict)
        if is_dict_update and denial.get("is_revoked") and not denial.get("is_revoked_comment"):
            raise serializers.ValidationError({"is_revoked_comment": "This field is required"})
        return validated_data

    def update(self, instance, validated_data):
        # This is required because the flattened columns are required to support the older denial screen
        # Serialisers don't support dotted fileds so we need to override. is_revoked and is_revoked_comments
        # are the only updates we support so this is ok.
        denial = validated_data.get("denial")
        if isinstance(denial, dict):
            if denial.get("is_revoked"):
                instance.denial.is_revoked = denial["is_revoked"]
                instance.denial.is_revoked_comment = validated_data["denial"]["is_revoked_comment"]
                instance.denial.save()
            elif denial.get("is_revoked") is False:
                instance.denial.is_revoked = denial["is_revoked"]
                instance.denial.is_revoked_comment = ""
                instance.denial.save()
        return instance


class DenialFromCSVFileSerializer(serializers.Serializer):
    csv_file = serializers.CharField()

    required_headers_denial_entity = [
        "name",
        "address",
        "country",
        "entity_type",
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

    @transaction.atomic
    def validate_csv_file(self, value):
        csv_file = io.StringIO(value)
        reader = csv.DictReader(csv_file)

        # Check if required headers are present
        if not (set(self.required_headers_denial_entity + self.required_headers_denial)).issubset(set(reader.fieldnames)):  # type: ignore
            raise serializers.ValidationError("Missing required headers in CSV file")

        logging_counts = {"denial": {"created": 0, "updated": 0}, "denial_entity": {"created": 0, "updated": 0}}
        logging_regime_reg_ref_values = {
            "denial": {"created": [], "updated": []},
            "denial_entity": {"created": [], "updated": []},
        }
        errors = []
        for i, row in enumerate(reader, start=1):
            denial_entity_data = {
                **{field: escape(row[field]) for field in self.required_headers_denial_entity},
                "created_by": self.context["request"].user,
            }

            denial_data = {**{field: escape(row[field].strip()) for field in self.required_headers_denial}}

            # Create a serializer instance to validate data

            denial_serializer = DenialSerializer(data=denial_data)
            is_valid_denial_data = denial_serializer.is_valid()

            if len(denial_serializer.errors) == 1 and denial_serializer.errors.get("regime_reg_ref"):
                # This is a bit of a hack presently we care about uniqueness but do want to validate the fields
                # Hence we override the check

                if (
                    hasattr(denial_serializer.errors["regime_reg_ref"][0], "code")
                    and denial_serializer.errors["regime_reg_ref"][0].code == "unique"
                ):
                    is_valid_denial_data = True

            if is_valid_denial_data:
                # Try to update an existing Denial record or create a new one
                regime_reg_ref = denial_serializer.data["regime_reg_ref"]
                denial, is_denial_created = models.Denial.objects.update_or_create(
                    regime_reg_ref=regime_reg_ref, defaults=denial_data
                )

                if is_denial_created:
                    logging_counts["denial"]["created"] += 1
                    logging_regime_reg_ref_values["denial"]["created"].append(denial.regime_reg_ref)
                else:
                    logging_counts["denial"]["updated"] += 1
                    logging_regime_reg_ref_values["denial"]["updated"].append(denial.regime_reg_ref)

                denial_entity_data.update({"denial": denial.id})
                denial_entity_serializer = DenialEntitySerializer(data=denial_entity_data)

                denial_entity_serializer.is_valid(raise_exception=True)
                # Now lets proceed with denial entity object

                # We assume that a DenialEntity object already exists if we can
                # match on all of the following fields
                denial_entity_lookup_fields = {
                    "name": denial_entity_serializer.validated_data["name"],
                    "address": denial_entity_serializer.validated_data["address"],
                    "entity_type": denial_entity_serializer.validated_data["entity_type"],
                }
                # Link the validated DenialEntity data with the Denial

                denial_entity_created_data = denial_entity_serializer.validated_data
                denial_entity_created_data["denial"] = denial
                denial_entity, is_denial_entity_created = models.DenialEntity.objects.update_or_create(
                    defaults=denial_entity_serializer.validated_data, denial=denial, **denial_entity_lookup_fields
                )

                if is_denial_entity_created:
                    logging_counts["denial_entity"]["created"] += 1
                    logging_regime_reg_ref_values["denial_entity"]["created"].append(
                        denial_entity.denial.regime_reg_ref
                    )
                else:
                    logging_counts["denial_entity"]["updated"] += 1
                    logging_regime_reg_ref_values["denial_entity"]["updated"].append(
                        denial_entity.denial.regime_reg_ref
                    )
            else:
                self.add_bulk_errors(errors, i, {**denial_serializer.errors})

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
    entity_type = KeyValueChoiceField(choices=models.DenialEntityType.choices, required=False)
    reference = serializers.ReadOnlyField(source="denial.reference")
    end_use = serializers.ReadOnlyField(source="denial.end_use")
    name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    item_description = serializers.SerializerMethodField()
    denial_cle = serializers.SerializerMethodField()
    search_score = serializers.SerializerMethodField()
    regime_reg_ref = serializers.SerializerMethodField()

    class Meta:
        document = documents.DenialEntityDocument
        fields = (
            "id",
            "address",
            "country",
            "name",
            "notifying_government",
            "item_description",
            "denial_cle",
            "regime_reg_ref",
        )

    def get_entity_type(self, obj):
        return get_denial_entity_type(obj.data.to_dict())

    def get_name(self, obj):
        return self.get_highlighted_field(obj, "name")

    def get_address(self, obj):
        return self.get_highlighted_field(obj, "address")

    def get_denial_cle(self, obj):
        return self.get_highlighted_field(obj, "denial_cle")

    def get_item_description(self, obj):
        return self.get_highlighted_field(obj, "item_description")

    def get_search_score(self, obj):
        return round(obj.meta.score, 2)

    def get_regime_reg_ref(self, obj):
        return self.get_highlighted_field(obj, "regime_reg_ref")

    def get_highlighted_field(self, obj, field_name):
        if hasattr(obj.meta, "highlight") and obj.meta.highlight.to_dict().get(field_name):
            return obj.meta.highlight.to_dict().get(field_name)[0]
        return getattr(obj, field_name)


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
