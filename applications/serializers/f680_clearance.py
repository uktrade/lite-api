from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from rest_framework.fields import CharField

from applications.enums import MTCRAnswers, ServiceEquipmentType
from applications.mixins.serializers import PartiesSerializerMixin
from applications.models import F680ClearanceApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationViewSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationListSerializer,
)
from applications.serializers.good import GoodOnApplicationViewSerializer
from conf.serializers import KeyValueChoiceField, PrimaryKeyRelatedSerializerField
from goods.enums import PvGrading
from lite_content.lite_api import strings
from static.f680_clearance_types.enums import F680ClearanceTypeEnum
from static.f680_clearance_types.models import F680ClearanceType


class F680ClearanceTypeSerializer(serializers.ModelSerializer):
    name = KeyValueChoiceField(choices=F680ClearanceTypeEnum.choices)

    class Meta:
        model = F680ClearanceType
        fields = ("name",)


class F680ClearanceViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    types = F680ClearanceTypeSerializer(read_only=True, many=True)
    clearance_level = KeyValueChoiceField(choices=PvGrading.choices, allow_null=True, required=False, allow_blank=True)

    expedited = serializers.BooleanField(required=False)
    expedited_date = serializers.DateField(required=False)
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

    prospect_value = serializers.DecimalField(required=False, allow_null=True, max_digits=15, decimal_places=2)

    class Meta:
        model = F680ClearanceApplication
        fields = GenericApplicationListSerializer.Meta.fields + (
            "case_officer",
            "end_user",
            "third_parties",
            "goods",
            "activity",
            "usage",
            "destinations",
            "additional_documents",
            "types",
            "clearance_level",
            "intended_end_use",
            "expedited",
            "expedited_date",
            "expedited_description",
            "foreign_technology",
            "foreign_technology_description",
            "locally_manufactured",
            "locally_manufactured_description",
            "mtcr_type",
            "electronic_warfare_requirement",
            "uk_service_equipment",
            "uk_service_equipment_description",
            "uk_service_equipment_type",
            "prospect_value",
        )


class F680ClearanceCreateSerializer(GenericApplicationCreateSerializer):
    class Meta:
        model = F680ClearanceApplication
        fields = (
            "id",
            "name",
            "case_type",
            "organisation",
            "status",
            "clearance_level",
        )


class F680ClearanceUpdateSerializer(GenericApplicationUpdateSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Applications.Generic.MISSING_REFERENCE_NAME_ERROR},
    )
    types = PrimaryKeyRelatedSerializerField(
        queryset=F680ClearanceType.objects.all(),
        serializer=F680ClearanceTypeSerializer,
        error_messages={"required": strings.Applications.F680.NO_CLEARANCE_TYPE},
        many=True,
    )
    clearance_level = serializers.ChoiceField(choices=PvGrading.choices, allow_null=True)

    expedited = serializers.BooleanField(required=False, allow_null=True)
    expedited_date = serializers.DateField(required=False)
    expedited_description = serializers.CharField(max_length=2000, allow_blank=True, required=False)

    foreign_technology = serializers.BooleanField(required=False, allow_null=True)
    foreign_technology_description = serializers.CharField(max_length=2000, allow_blank=True, required=False)

    locally_manufactured = serializers.BooleanField(required=False, allow_null=True)
    locally_manufactured_description = serializers.CharField(max_length=2000, allow_blank=True, required=False)

    mtcr_type = KeyValueChoiceField(choices=MTCRAnswers.choices(), allow_blank=True, required=False)

    electronic_warfare_requirement = serializers.BooleanField(required=False, allow_null=True)

    uk_service_equipment = serializers.BooleanField(required=False, allow_null=True)
    uk_service_equipment_description = serializers.CharField(max_length=2000, allow_blank=True, required=False)
    uk_service_equipment_type = KeyValueChoiceField(
        choices=ServiceEquipmentType.choices(), allow_blank=True, required=False
    )

    prospect_value = serializers.DecimalField(required=False, allow_null=True, max_digits=15, decimal_places=2)

    class Meta:
        model = F680ClearanceApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + (
            "types",
            "clearance_level",
            "expedited",
            "expedited_date",
            "expedited_description",
            "foreign_technology",
            "foreign_technology_description",
            "locally_manufactured",
            "locally_manufactured_description",
            "mtcr_type",
            "electronic_warfare_requirement",
            "uk_service_equipment",
            "uk_service_equipment_description",
            "uk_service_equipment_type",
            "prospect_value",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "types" in self.initial_data:
            self.initial_data["types"] = [
                F680ClearanceTypeEnum.ids.get(clearance_type) for clearance_type in self.initial_data.get("types", [])
            ]

    def validate(self, data):
        required_fields = [
            "expedited",
            "foreign_technology",
            "locally_manufactured",
            "mtcr_type",
            "electronic_warfare_requirement",
            "uk_service_equipment",
            "prospect_value"
        ]
        required_secondary_fields = {
            "foreign_technology": "foreign_technology_description",
            "expedited": "expedited_date",
            "locally_manufactured": "locally_manufactured_description",
        }
        error_messages = {
            "expedited": "Select yes if you need the F680 clearance in less than 30 days",
            "expedited_date": "Enter the date you need the clearance",
            "foreign_technology": "Select yes if any foreign technology or information involved in the release",
            "foreign_technology_description": "Enter details",
            "locally_manufactured": "Select yes if local assembly or manufacture is required",
            "locally_manufactured_description": "Enter details",
            "mtcr_type": "Select yes if you believe the products are rated under the MTCR",
            "electronic_warfare_requirement": "Select yes if there’s a requirement to release UK MOD owned EW data or information in support of the export",
            "uk_service_equipment": "Select yes if the equipment is in service with the UK armed forces",
            "uk_service_equipment_type": "Select how the product is funded",
            "prospect_value": "Please enter value",
        }
        for field in required_fields:
            if field in self.initial_data:
                if self.initial_data[field] is None or self.initial_data[field] == '':
                    raise serializers.ValidationError({field: [error_messages[field]]})
                if self.initial_data[field] is True:
                    secondary_field = required_secondary_fields.get(field, False)
                    if secondary_field and not self.initial_data.get(secondary_field):
                        raise serializers.ValidationError({secondary_field: [error_messages[secondary_field]]})

        validated_data = super().validate(data)

        if "types" in self.initial_data and not validated_data.get("types"):
            raise serializers.ValidationError({"types": strings.Applications.F680.NO_CLEARANCE_TYPE})

        if validated_data.get("expedited"):
            today = timezone.now().date()
            limit = (timezone.now() + timedelta(days=30)).date()
            if today > validated_data["expedited_date"] or validated_data["expedited_date"] > limit:
                raise serializers.ValidationError({"expedited_date": ["Date must be within 30 days."]})

            validated_data["expedited_date"] = str(validated_data["expedited_date"])

        return validated_data

    def update(self, instance, validated_data):
        if "types" in validated_data:
            validated_data["types"] = validated_data.get("types")

        instance = super().update(instance, validated_data)
        return instance
