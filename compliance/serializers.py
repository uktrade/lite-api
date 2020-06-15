from rest_framework import serializers

from addresses.serializers import AddressSerializer
from cases.libraries.get_flags import get_ordered_flags
from cases.models import Case
from compliance.models import ComplianceSiteCase
from conf.serializers import PrimaryKeyRelatedSerializerField
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum
from teams.helpers import get_team_by_pk


class ComplianceSiteViewSerializer(serializers.ModelSerializer):
    site = AddressSerializer(source="site.address")
    status = serializers.SerializerMethodField()
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=OrganisationDetailSerializer
    )

    class Meta:
        model = ComplianceSiteCase
        fields = (
            "site",
            "status",
            "organisation",
        )

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None


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
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None
