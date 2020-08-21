from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.applications.mixins.serializers import PartiesSerializerMixin
from api.applications.models import ExhibitionClearanceApplication
from api.applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationViewSerializer,
    GenericApplicationUpdateSerializer,
)
from api.applications.serializers.good import GoodOnApplicationViewSerializer
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
    title = serializers.CharField(
        max_length=255,
        allow_null=False,
        error_messages={
            "blank": strings.Applications.Exhibition.Error.NO_EXHIBITION_NAME,
            "required": strings.Applications.Exhibition.Error.NO_EXHIBITION_NAME,
            "null": strings.Applications.Exhibition.Error.NO_EXHIBITION_NAME,
        },
    )
    first_exhibition_date = serializers.DateField(
        allow_null=False,
        error_messages={
            "invalid": strings.Applications.Exhibition.Error.BLANK_EXHIBITION_START_DATE,
            "required": strings.Applications.Exhibition.Error.NO_EXHIBITION_START_DATE,
            "null": strings.Applications.Exhibition.Error.NO_EXHIBITION_START_DATE,
        },
    )
    required_by_date = serializers.DateField(
        allow_null=False,
        error_messages={
            "invalid": strings.Applications.Exhibition.Error.BLANK_REQUIRED_BY_DATE,
            "required": strings.Applications.Exhibition.Error.NO_REQUIRED_BY_DATE,
            "null": strings.Applications.Exhibition.Error.NO_REQUIRED_BY_DATE,
        },
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

    def validate(self, data):
        required_by_date_errors = []
        first_exhibition_date_errors = []

        today = timezone.now().date()
        if data["required_by_date"] < today:
            required_by_date_errors.append(strings.Applications.Exhibition.Error.REQUIRED_BY_DATE_FUTURE)
        if data["first_exhibition_date"] < today:
            first_exhibition_date_errors.append(strings.Applications.Exhibition.Error.FIRST_EXHIBITION_DATE_FUTURE)

        if not first_exhibition_date_errors and data["required_by_date"] > data["first_exhibition_date"]:
            first_exhibition_date_errors.append(
                strings.Applications.Exhibition.Error.REQUIRED_BY_BEFORE_FIRST_EXHIBITION_DATE
            )

        errors = {}
        if first_exhibition_date_errors:
            errors.update({"first_exhibition_date": first_exhibition_date_errors})
        if required_by_date_errors:
            errors.update({"required_by_date": required_by_date_errors})
        if errors:
            raise ValidationError(errors)

        return data
