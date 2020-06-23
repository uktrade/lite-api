from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from addresses.serializers import AddressSerializer
from cases.models import Case
from compliance.models import ComplianceSiteCase
from conf.serializers import PrimaryKeyRelatedSerializerField
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer

from cases.libraries.get_flags import get_ordered_flags
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum
from teams.helpers import get_team_by_pk

from compliance.models import OpenLicenceReturns
from lite_content.lite_api.strings import Compliance


class ComplianceSiteViewSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source="site.name")
    address = AddressSerializer(source="site.address")
    status = serializers.SerializerMethodField()
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=OrganisationDetailSerializer
    )
    open_licence_returns = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceSiteCase
        fields = (
            "address",
            "site_name",
            "status",
            "organisation",
            "open_licence_returns",
        )

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None

    def get_open_licence_returns(self, instance):
        queryset = OpenLicenceReturns.objects.filter(organisation_id=instance.organisation_id).order_by(
            "-year", "-created_at"
        )

        return OpenLicenceReturnsListSerializer(queryset, many=True).data


class ComplianceLicenceListSerializer(serializers.ModelSerializer):
    flags = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    team = None

    class Meta:
        model = Case
        fields = (
            "id",
            "reference_code",
            "status",
            "flags",
        )

    def __init__(self, *args, **kwargs):
        super(ComplianceLicenceListSerializer, self).__init__(*args, **kwargs)

        self.team = get_team_by_pk(self.context.get("request").user.team_id)

    def get_flags(self, instance):
        return get_ordered_flags(case=instance, team=self.team, limit=3)

    def get_status(self, instance):
        # Temporarily display the case status, until licence status story is played.
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None


class OpenLicenceReturnsListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    year = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class OpenLicenceReturnsViewSerializer(OpenLicenceReturnsListSerializer):
    returns_data = serializers.CharField()


class OpenLicenceReturnsCreateSerializer(serializers.ModelSerializer):
    returns_data = serializers.CharField(required=True, allow_blank=False)
    year = serializers.IntegerField(
        required=True, error_messages={"required": Compliance.OpenLicenceReturns.YEAR_ERROR}
    )

    class Meta:
        model = OpenLicenceReturns
        fields = (
            "id",
            "returns_data",
            "year",
            "organisation",
            "licences",
        )

    def validate_year(self, value):
        current_year = timezone.now().year
        last_year = current_year - 1

        if value not in [current_year, last_year]:
            raise ValidationError(Compliance.OpenLicenceReturns.INVALID_YEAR)

        return value
