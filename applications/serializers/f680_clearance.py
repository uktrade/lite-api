from rest_framework import serializers
from rest_framework.fields import CharField

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

    class Meta:
        model = F680ClearanceApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + ("types", "clearance_level",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "types" in self.initial_data:
            self.initial_data["types"] = [
                F680ClearanceTypeEnum.ids.get(clearance_type) for clearance_type in self.initial_data.get("types", [])
            ]

    def validate(self, data):
        validated_data = super().validate(data)

        if "types" in self.initial_data and not validated_data.get("types"):
            raise serializers.ValidationError({"types": strings.Applications.F680.NO_CLEARANCE_TYPE})

        return validated_data

    def update(self, instance, validated_data):
        if "types" in validated_data:
            validated_data["types"] = validated_data.get("types")

        instance = super().update(instance, validated_data)
        return instance
