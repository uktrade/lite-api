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
from conf.serializers import KeyValueChoiceField
from goods.enums import PvGrading
from lite_content.lite_api import strings


class F680ClearanceViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
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
            "clearance_level",
        )


class F680ClearanceCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, case_type_id, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["case_type"] = case_type_id

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
        error_messages={"blank": strings.Applications.MISSING_REFERENCE_NAME_ERROR},
    )
    clearance_level = serializers.ChoiceField(choices=PvGrading.choices, allow_null=True)

    class Meta:
        model = F680ClearanceApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + ("clearance_level",)
