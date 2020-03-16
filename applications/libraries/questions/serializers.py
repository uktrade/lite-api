import uuid

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from applications.enums import MTCRAnswers
from conf.serializers import KeyValueChoiceField


class F680JsonSerializer(serializers.Serializer):
    expedited = serializers.BooleanField(required=False)
    expedited_date = serializers.DateField(required=False, format="DD-MM-YYYY")

    foreign_technology = serializers.BooleanField(required=False)
    foreign_technology_description = serializers.CharField(max_length=256, allow_blank=True, required=False)

    locally_manufactured = serializers.BooleanField(required=False)
    locally_manufactured_description = serializers.CharField(max_length=256, allow_blank=True, required=False)

    mtcr_type = KeyValueChoiceField(choices=MTCRAnswers.choices(), allow_blank=True, required=False)

    electronic_warfare_requirement = serializers.BooleanField(required=False)
    electronic_warfare_requirement_attachment = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    # electronic_warfare_requirement_attachment = serializers.UUIDField(required=False, allow_null=True)

    uk_service_equipment = serializers.BooleanField(required=False)
    uk_service_equipment_description = serializers.CharField(max_length=256, allow_blank=True, required=False)
    uk_service_equipment_type = serializers.CharField(required=False, allow_blank=True)

    value = serializers.IntegerField(required=False)


    def validate(self, attrs):
        if attrs.get("electronic_warfare_requirement"):
            try:
                uuid.UUID(attrs.get("electronic_warfare_requirement_attachment"))
            except (ValueError, TypeError):
                raise ValidationError({"electronic_warfare_requirement_attachment": ["Attachment required."]})

        if attrs.get("expedited") and not attrs.get("expedited_date"):
            raise ValidationError({"expedited_date": ["Date required."]})

        return attrs

    def validate_electronic_warfare_requirement_attachment(self, item):
        try:
            uuid.UUID(item)
        except (ValueError, TypeError):
            raise ValidationError({"electronic_warfare_requirement_attachment": ["Must be a valid UUID"]})

        return item
