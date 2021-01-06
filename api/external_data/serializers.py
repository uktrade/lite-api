import csv
import io

from django.db import transaction

from rest_framework import serializers

from api.external_data import models


class ComplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Denial
        fields = (
            "created_by",
            "denied_name",
            "authority",
            "data",
        )


class DenialFromCSVFileSerializer(serializers.Serializer):

    csv_file = serializers.FileField()

    @transaction.atomic
    def validate_csv_file(self, memory_file):
        csv_file = io.TextIOWrapper(memory_file, encoding="utf-8")
        dialect = csv.Sniffer().sniff(csv_file.read(1024))
        csv_file.seek(0)
        reader = csv.reader(csv_file, dialect=dialect)
        headers = next(reader, None)
        errors = []
        for i, row in enumerate(reader):
            serializer = ComplianceSerializer(
                data={
                    "authority": row[0],
                    "denied_name": row[1],
                    "data": dict(zip(headers, row[2:])),
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
        return memory_file

    @staticmethod
    def add_bulk_errors(errors, row_number, line_errors):
        errors.append("[Row {number}] {errors}".format(errors=json.dumps(line_errors), number=row_number,))
