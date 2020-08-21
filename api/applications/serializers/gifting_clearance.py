from rest_framework import serializers
from rest_framework.fields import CharField

from api.applications.mixins.serializers import PartiesSerializerMixin
from api.applications.models import GiftingClearanceApplication
from api.applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from api.applications.serializers.good import GoodOnApplicationViewSerializer
from lite_content.lite_api import strings


class GiftingClearanceViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()

    class Meta:
        model = GiftingClearanceApplication
        fields = GenericApplicationViewSerializer.Meta.fields + (
            "case_officer",
            "end_user",
            "third_parties",
            "goods",
            "activity",
            "usage",
            "destinations",
            "additional_documents",
        )


class GiftingClearanceCreateSerializer(GenericApplicationCreateSerializer):
    class Meta:
        model = GiftingClearanceApplication
        fields = (
            "id",
            "name",
            "case_type",
            "organisation",
            "status",
        )


class GiftingClearanceUpdateSerializer(GenericApplicationUpdateSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Applications.Generic.MISSING_REFERENCE_NAME_ERROR},
    )

    class Meta:
        model = GiftingClearanceApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields
