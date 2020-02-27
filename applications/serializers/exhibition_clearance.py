from rest_framework import serializers
from rest_framework.fields import CharField

from applications.mixins.serializers import PartiesSerializerMixin
from applications.models import ExhibitionClearanceApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationViewSerializer,
    GenericApplicationUpdateSerializer,
)
from applications.serializers.good import GoodOnApplicationViewSerializer
from lite_content.lite_api import strings


class ExhibitionClearanceViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()

    class Meta:
        model = ExhibitionClearanceApplication
        fields = (
            GenericApplicationViewSerializer.Meta.fields
            + PartiesSerializerMixin.Meta.fields
            + ("goods", "activity", "usage", "destinations", "additional_documents",)
        )


class ExhibitionClearanceCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, case_type_id, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["case_type"] = case_type_id

    class Meta:
        model = ExhibitionClearanceApplication
        fields = (
            "id",
            "name",
            "case_type",
            "organisation",
            "status",
        )


class ExhibitionClearanceUpdateSerializer(GenericApplicationUpdateSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Applications.MISSING_REFERENCE_NAME_ERROR},
    )

    class Meta:
        model = ExhibitionClearanceApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields
