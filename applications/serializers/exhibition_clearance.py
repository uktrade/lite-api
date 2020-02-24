import datetime

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
from lite_content.lite_api import strings


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
            "title",
            "first_exhibition_date",
            "required_by_date",
            "reason_for_clearance",
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
    first_exhibition_date = serializers.DateField(
        allow_null=False,
        error_messages={"invalid": "Enter the first exhibition's date and include a day, month, year."},
    )
    required_by_date = serializers.DateField(
        allow_null=False, error_messages={"invalid": "Enter the required by date and include a day, month, year."},
    )
    reason_for_clearance = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)

    class Meta:
        model = ExhibitionClearanceApplication
        fields = (
            "title",
            "first_exhibition_date",
            "required_by_date",
            "reason_for_clearance",
        )

    def validate_first_exhibition_date(self, value):
        if value <= datetime.date.today():
            raise serializers.ValidationError(strings.Applications.Exhibition.Error.FIRST_EXHIBITION_DATE_FUTURE)
        elif (
            value < datetime.datetime.strptime(self.initial_data["required_by_date"].replace("-", ""), "%Y%m%d").date()
        ):
            raise serializers.ValidationError(
                strings.Applications.Exhibition.Error.REQUIRED_BY_BEFORE_FIRST_EXHIBITION_DATE
            )
        return value

    def validate_required_by_date(self, value):
        if value <= datetime.date.today():
            raise serializers.ValidationError(strings.Applications.Exhibition.Error.REQUIRED_BY_DATE_FUTURE)
        return value
