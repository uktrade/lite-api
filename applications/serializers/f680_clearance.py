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
from cases.enums import CaseTypeEnum
from lite_content.lite_api import strings


class F680ClearanceViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()

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
        )


class F680ClearanceCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["case_type"] = CaseTypeEnum.F680.id

    class Meta:
        model = F680ClearanceApplication
        fields = (
            "id",
            "name",
            "case_type",
            "organisation",
            "status",
        )


class F680ClearanceUpdateSerializer(GenericApplicationUpdateSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Applications.MISSING_REFERENCE_NAME_ERROR},
    )

    class Meta:
        model = F680ClearanceApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields
