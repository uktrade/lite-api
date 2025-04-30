from rest_framework import serializers

from api.applications.enums import (
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
)
from api.applications.models import BaseApplication
from api.cases.enums import CaseTypeSubTypeEnum
from api.cases.serializers import CaseTypeSerializer
from api.core.helpers import get_value_from_enum
from api.core.serializers import KeyValueChoiceField
from lite_content.lite_api import strings

from .fields import CaseStatusField


class GenericApplicationListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    case_type = CaseTypeSerializer()
    status = CaseStatusField()
    submitted_at = serializers.DateTimeField()
    submitted_by = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField()
    reference_code = serializers.CharField()
    export_type = serializers.SerializerMethodField()

    def get_export_type(self, instance):
        if hasattr(instance, "export_type") and getattr(instance, "export_type"):
            return {
                "key": instance.export_type,
                "value": get_value_from_enum(instance.export_type, ApplicationExportType),
            }

    def get_submitted_by(self, instance):
        return f"{instance.submitted_by.full_name}" if instance.submitted_by else ""


class GenericApplicationCopySerializer(serializers.ModelSerializer):
    """
    Serializer for copying applications that can handle any application type

    This is only used to verify the fields are correct that the user passes in, we then process the rest of the
     copy after validation
    """

    name = serializers.CharField(allow_null=False, allow_blank=False)
    have_you_been_informed = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    reference_number_on_information_form = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=255
    )

    class Meta:
        model = BaseApplication
        fields = (
            "name",
            "have_you_been_informed",
            "reference_number_on_information_form",
        )

    def __init__(self, context=None, *args, **kwargs):

        if context and context.get("application_type").sub_type == CaseTypeSubTypeEnum.STANDARD:
            self.fields["have_you_been_informed"] = KeyValueChoiceField(
                required=True,
                choices=ApplicationExportLicenceOfficialType.choices,
                error_messages={"required": strings.Goods.INFORMED},
            )
            if kwargs.get("data").get("have_you_been_informed") == ApplicationExportLicenceOfficialType.YES:
                self.fields["reference_number_on_information_form"] = serializers.CharField(
                    required=True, allow_blank=True, max_length=255
                )

        super().__init__(*args, **kwargs)
