from rest_framework import serializers
from rest_framework.fields import CharField

from applications.models import FSixEightyClearanceApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationViewSerializer,
    GenericApplicationUpdateSerializer,
)
from applications.serializers.good import GoodOnApplicationViewSerializer
from cases.enums import CaseTypeEnum
from lite_content.lite_api import strings
from parties.serializers import (
    EndUserWithFlagsSerializer,
    ThirdPartyWithFlagsSerializer,
)


class FSixEightyClearanceViewSerializer(GenericApplicationViewSerializer):
    end_user = EndUserWithFlagsSerializer()
    third_parties = ThirdPartyWithFlagsSerializer(many=True)
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()

    class Meta:
        model = FSixEightyClearanceApplication
        fields = GenericApplicationViewSerializer.Meta.fields + (
            "end_user",
            "third_parties",
            "goods",
            "activity",
            "usage",
            "destinations",
            "additional_documents",
        )


class FSixEightyClearanceCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["type"] = CaseTypeEnum.GIFTING_CLEARANCE

    class Meta:
        model = FSixEightyClearanceApplication
        fields = (
            "id",
            "name",
            "application_type",
            "organisation",
            "type",
            "status",
        )


class FSixEightyClearanceUpdateSerializer(GenericApplicationUpdateSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Applications.MISSING_REFERENCE_NAME_ERROR},
    )

    class Meta:
        model = FSixEightyClearanceApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields
