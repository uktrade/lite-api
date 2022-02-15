from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.cases.enums import CaseTypeEnum
from api.cases.models import CaseType
from api.cases.serializers import CaseTypeSerializer
from api.core.serializers import ControlListEntryField, KeyValueChoiceField, PrimaryKeyRelatedSerializerField
from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from lite_content.lite_api.strings import OpenGeneralLicences
from api.open_general_licences.enums import OpenGeneralLicenceStatus
from api.open_general_licences.models import OpenGeneralLicence
from api.organisations.serializers import SiteListSerializer
from api.staticdata.countries.models import Country
from api.staticdata.countries.serializers import CountrySerializer
from api.staticdata.statuses.libraries.get_case_status import get_status_value_from_case_status_enum


class OpenGeneralLicenceCaseListSerializer(serializers.Serializer):
    reference_code = serializers.CharField()
    site = SiteListSerializer()
    status = serializers.SerializerMethodField()
    submitted_at = serializers.DateTimeField()

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }


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
        queryset=CaseType.objects.filter(id__in=CaseTypeEnum.OPEN_GENERAL_LICENCE_IDS).all(),
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
    control_list_entries = ControlListEntryField(
        many=True,
        required=True,
        allow_empty=False,
    )
    registration_required = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"invalid": OpenGeneralLicences.serializerErrors.REQUIRED_REGISTRATION_REQUIRED},
    )
    status = KeyValueChoiceField(choices=OpenGeneralLicenceStatus.choices, required=False)
    registrations = serializers.SerializerMethodField()

    def get_registrations(self, instance):
        if self.context and "cases" in self.context:
            cases = self.context["cases"]
            data = []
            for case in cases:
                if case.open_general_licence_id == instance.id:
                    try:
                        licence = Licence.objects.get_active_licence(case)
                    except Licence.DoesNotExist:
                        licence = Licence.objects.order_by("-created_at").first()

                    data.append(
                        {
                            "reference_code": licence.reference_code,
                            "site": {
                                "id": case.site.id,
                                "name": case.site.name,
                                "address": {
                                    "address_line_1": case.site.address.address_line_1,
                                    "address_line_2": case.site.address.address_line_2,
                                    "city": case.site.address.city,
                                    "region": case.site.address.region,
                                    "postcode": case.site.address.postcode,
                                    "country": {
                                        "name": "United Kingdom",
                                    },
                                },
                                "records_located_at": {"name": case.records_located_at_name},
                            },
                            "status": {
                                "key": licence.status,
                                "value": LicenceStatus.to_str(licence.status),
                            },
                            "submitted_at": case.submitted_at,
                        }
                    )
            return data

    class Meta:
        model = OpenGeneralLicence
        fields = "__all__"

    def validate_url(self, url):
        if "gov.uk" not in url.lower():
            raise serializers.ValidationError(OpenGeneralLicences.serializerErrors.NON_GOV_URL)

        return url
