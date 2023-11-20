import csv
import io

from django.db import transaction

from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from api.external_data import documents, models
from api.external_data.helpers import get_denial_entity_type
from api.flags.enums import SystemFlags


class DenialSerializer(serializers.ModelSerializer):
    entity_type = serializers.SerializerMethodField()

    class Meta:
        model = models.Denial
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
            serializer = DenialSerializer(
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
