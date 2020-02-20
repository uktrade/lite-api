from rest_framework import serializers

from applications.mixins.serializers import PartiesSerializerMixin
from applications.models import ExhibitionClearanceApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationViewSerializer,
    GenericApplicationUpdateSerializer,
)
from applications.serializers.good import GoodOnApplicationViewSerializer
from cases.enums import CaseTypeEnum


class ExhibitionClearanceViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()

    class Meta:
        model = ExhibitionClearanceApplication
        fields = GenericApplicationViewSerializer.Meta.fields + (
            "goods",
            "activity",
            "usage",
            "destinations",
            "additional_documents",
        )


class ExhibitionClearanceCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["case_type"] = CaseTypeEnum.EXHIBITION.id

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
    title = serializers.CharField(required=True, max_length=255)
    first_exhibition_date = serializers.DateField(required=True)
    required_by_date = serializers.DateField(required=True)
    reason_for_clearance = serializers.CharField(max_length=2000)

    class Meta:
        model = ExhibitionClearanceApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + (
            "title",
            "first_exhibition_date",
            "required_by_date",
            "reason_for_clearance",
        )


class ExhibitionClearanceDetailSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True, max_length=255)
    first_exhibition_date = serializers.DateField(required=True)
    required_by_date = serializers.DateField(required=True)
    reason_for_clearance = serializers.CharField(max_length=2000)

    class Meta:
        model = ExhibitionClearanceApplication
        fields = (
            "title",
            "first_exhibition_date",
            "required_by_date",
            "reason_for_clearance",
        )
