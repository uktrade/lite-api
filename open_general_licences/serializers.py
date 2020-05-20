from rest_framework import serializers

from cases.models import CaseType
from conf.serializers import ControlListEntryField, KeyValueChoiceField
from open_general_licences.enums import OpenGeneralLicenceStatus
from open_general_licences.models import OpenGeneralLicence
from static.countries.models import Country


class OpenGeneralLicenceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        required=True, allow_blank=False, allow_null=False, max_length=250, error_messages={"blank": "Enter a name"}
    )
    description = serializers.CharField(
        required=True, allow_blank=False, allow_null=False, error_messages={"blank": "Enter description"}
    )
    url = serializers.URLField(
        required=True, allow_blank=False, allow_null=False, error_messages={"blank": "Enter url"}
    )
    case_type = serializers.PrimaryKeyRelatedField(
        queryset=CaseType.objects.all(),
        required=True,
        allow_null=False,
        allow_empty=False,
        error_messages={"required": "Select type of OGL"},
    )
    countries = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        many=True,
        required=True,
        allow_null=False,
        allow_empty=False,
        error_messages={"required": "Select countries"},
    )
    control_list_entries = ControlListEntryField(many=True, required=True, allow_empty=False)
    registration_required = serializers.BooleanField(required=True, allow_null=False)
    status = KeyValueChoiceField(choices=OpenGeneralLicenceStatus.choices, required=False)

    class Meta:
        model = OpenGeneralLicence
        fields = "__all__"

    def validate_url(self, url):
        if "gov.uk" not in url.lower():
            raise serializers.ValidationError("Has to be on the gov uk domain")

        return url
