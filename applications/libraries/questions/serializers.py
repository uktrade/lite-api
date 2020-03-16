from rest_framework import serializers

from applications.enums import MTCRAnswers
from conf.serializers import KeyValueChoiceField


class F680JsonSerializer(serializers.Serializer):
    expedited = serializers.BooleanField(required=False)
    expedited_description = serializers.CharField(max_length=256, allow_blank=True, required=False)

    foreign_technology = serializers.BooleanField(required=False)
    foreign_technology_description = serializers.CharField(max_length=256, allow_blank=True, required=False)

    locally_manufactured = serializers.BooleanField(required=False)
    locally_manufactured_description = serializers.CharField(max_length=256, allow_blank=True, required=False)

    mtcr_type = KeyValueChoiceField(choices=MTCRAnswers.choices(), allow_blank=True, required=False)

    electronic_warfare_requirement = serializers.BooleanField(required=False)
    electronic_warfare_requirement_attachment = serializers.UUIDField(required=False)

    uk_service_equipment = serializers.BooleanField(required=False)
    uk_service_equipment_description = serializers.CharField(max_length=256, allow_blank=True, required=False)
    uk_service_equipment_type = serializers.CharField(required=False, allow_blank=True)

    value = serializers.IntegerField(required=False)
