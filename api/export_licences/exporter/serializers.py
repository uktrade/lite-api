from rest_framework import serializers

from api.applications.models import StandardApplication
from api.cases.enums import (
    CaseTypeEnum,
    CaseTypeReferenceEnum,
)
from api.cases.models import CaseType


class ExportLicenceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": "Enter a reference name for the application"},
    )
    licence_type = serializers.ChoiceField(
        choices=((CaseTypeReferenceEnum.SIEL, "SEIL"),),
        required=False,
    )

    class Meta:
        model = StandardApplication
        fields = [
            "id",
            "name",
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "licence_type",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "have_you_been_informed": {"required": True},
        }

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        validated_data["status"] = self.context["default_status"]
        licence_type = validated_data.pop("licence_type", CaseTypeReferenceEnum.EXPORT_LICENCE)
        case_type_id = CaseTypeEnum.reference_to_class(licence_type).id
        validated_data["case_type"] = CaseType.objects.get(pk=case_type_id)
        return super().create(validated_data)
