from datetime import timedelta

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from applications.enums import MTCRAnswers, ServiceEquipmentType
from conf.serializers import KeyValueChoiceField
from django.utils import timezone


class F680JsonSerializer(serializers.Serializer):
    expedited = serializers.BooleanField(required=False)
    expedited_date = serializers.DateField(required=False, format="DD-MM-YYYY")
    expedited_description = serializers.CharField(max_length=2000, allow_blank=True, required=False)

    foreign_technology = serializers.BooleanField(required=False)
    foreign_technology_description = serializers.CharField(max_length=2000, allow_blank=True, required=False)

    locally_manufactured = serializers.BooleanField(required=False)
    locally_manufactured_description = serializers.CharField(max_length=2000, allow_blank=True, required=False)

    mtcr_type = KeyValueChoiceField(choices=MTCRAnswers.choices(), allow_blank=True, required=False)

    electronic_warfare_requirement = serializers.BooleanField(required=False)

    uk_service_equipment = serializers.BooleanField(required=False)
    uk_service_equipment_description = serializers.CharField(max_length=2000, allow_blank=True, required=False)
    uk_service_equipment_type = KeyValueChoiceField(
        choices=ServiceEquipmentType.choices(), allow_blank=True, required=False
    )

    value = serializers.IntegerField(required=False)

    def validate(self, data):
        validated_data = super().validate(data)
        if validated_data.get("expedited"):
            if not validated_data.get("expedited_date"):
                raise ValidationError({"expedited_date": ["Date required."]})
            else:
                today = timezone.now().date()
                limit = (timezone.now() + timedelta(days=30)).date()
                if today >= validated_data["expedited_date"] or validated_data["expedited_date"] > limit:
                    raise ValidationError({"expedited_date": ["Date must be within 30 days."]})

                validated_data["expedited_date"] = str(validated_data["expedited_date"])

        if validated_data.get("foreign_technology") and not validated_data.get("foreign_technology_description"):
            raise ValidationError({"foreign_technology_description": ["Description required"]})

        if validated_data.get("locally_manufactured") and not validated_data.get("locally_manufactured_description"):
            raise ValidationError({"locally_manufactured_description": ["Description required"]})

        if validated_data.get("uk_service_equipment") and not validated_data.get("uk_service_equipment_type"):
            raise ValidationError({"uk_service_equipment_type": ["Please select an option"]})

        return validated_data

    def get_expedited_date(self, item):
        return str(item)
