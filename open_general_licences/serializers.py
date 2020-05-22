from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cases.enums import CaseTypeEnum
from cases.models import CaseType
from cases.serializers import CaseTypeSerializer
from conf.serializers import ControlListEntryField, KeyValueChoiceField, PrimaryKeyRelatedSerializerField
from lite_content.lite_api.strings import OpenGeneralLicences
from open_general_licences.enums import OpenGeneralLicenceStatus
from open_general_licences.models import OpenGeneralLicence
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class OpenGeneralLicenceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        max_length=250,
        error_messages={"blank": OpenGeneralLicences.serializerErrors.BLANK_NAME},
        validators=[
            UniqueValidator(
                queryset=OpenGeneralLicence.objects.all(), message=OpenGeneralLicences.serializerErrors.NON_UNIQUE_NAME
            )
        ],
    )
    description = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": OpenGeneralLicences.serializerErrors.BLANK_DESCRIPTION},
    )
    url = serializers.URLField(
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": OpenGeneralLicences.serializerErrors.BLANK_URL},
    )
    case_type = PrimaryKeyRelatedSerializerField(
        queryset=CaseType.objects.filter(id__in=CaseTypeEnum.OGL_ID_LIST).all(),
        required=True,
        allow_null=False,
        allow_empty=False,
        error_messages={"null": OpenGeneralLicences.serializerErrors.REQUIRED_CASE_TYPE},
        serializer=CaseTypeSerializer,
    )
    countries = PrimaryKeyRelatedSerializerField(
        queryset=Country.objects.all(),
        many=True,
        required=True,
        allow_null=False,
        allow_empty=False,
        error_messages={"required": OpenGeneralLicences.serializerErrors.REQUIRED_COUNTRIES},
        serializer=CountrySerializer,
    )
    control_list_entries = ControlListEntryField(many=True, required=True, allow_empty=False,)
    registration_required = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"invalid": OpenGeneralLicences.serializerErrors.REQUIRED_REGISTRATION_REQUIRED},
    )
    status = KeyValueChoiceField(choices=OpenGeneralLicenceStatus.choices, required=False)

    class Meta:
        model = OpenGeneralLicence
        fields = "__all__"

    def validate_url(self, url):
        if "gov.uk" not in url.lower():
            raise serializers.ValidationError(OpenGeneralLicences.serializerErrors.NON_GOV_URL)

        return url
