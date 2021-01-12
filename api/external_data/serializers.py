import csv
import json
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
            "data",
        )


class DenialFromCSVFileSerializer(serializers.Serializer):

    csv_file = serializers.CharField()

    @transaction.atomic
    def validate_csv_file(self, value):
        csv_file = io.StringIO(value)
        dialect = csv.Sniffer().sniff(csv_file.read(1024))
        csv_file.seek(0)
        reader = csv.reader(csv_file, dialect=dialect)
        headers = next(reader, None)
        errors = []
        for i, row in enumerate(reader):
            data = dict(zip(headers, row))
            serializer = DenialSerializer(
                data={
                    "reference": data.pop("reference", None),
                    "name": data.pop("name", None),
                    "address": data.pop("address", None),
                    "data": data,
                    "created_by": self.context["request"].user,
                }
            )

            if serializer.is_valid():
                serializer.save()
            else:
                self.add_bulk_errors(
                    errors=errors, row_number=i + 2, line_errors=serializer.errors,
                )
        if errors:
            raise serializers.ValidationError(errors)
        return csv_file

    @staticmethod
    def add_bulk_errors(errors, row_number, line_errors):
        errors.append("[Row {number}] {errors}".format(errors=json.dumps(line_errors), number=row_number,))


class DenialSearchSerializer(DocumentSerializer):
    class Meta:
        document = documents.DenialDocumentType
        fields = ("denied_name",)
