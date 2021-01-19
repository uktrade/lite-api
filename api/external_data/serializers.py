import csv
import io

from django.db import transaction

from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from api.external_data import documents, models


class DenialSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Denial
        fields = (
            "id",
            "created_by",
            "name",
            "address",
            "reference",
            "notifying_government",
            "final_destination",
            "item_list_codes",
            "item_description",
            "consignee_name",
            "end_use",
            "data",
            "is_revoked",
            "is_revoked_comment",
        )
        extra_kwargs = {
            "is_revoked": {"required": False},
            "is_revoked_comment": {"required": False},
        }

    def validate(self, data):
        validated_data = super().validate(data)
        if validated_data.get("is_revoked") and not validated_data.get("is_revoked_comment"):
            raise serializers.ValidationError({"is_revoked_comment": "This field is required"})
        return validated_data


class DenialFromCSVFileSerializer(serializers.Serializer):

    csv_file = serializers.CharField()
    required_headers = [
        "reference",
        "name",
        "address",
        "notifying_government",
        "final_destination",
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
    class Meta:
        document = documents.DenialDocumentType
        fields = ("denied_name",)
