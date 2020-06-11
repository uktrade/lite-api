from rest_framework import serializers

from addresses.serializers import AddressSerializer
from cases.models import Case
from compliance.models import ComplianceSiteCase
from conf.serializers import PrimaryKeyRelatedSerializerField
from licences.models import Licence
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum


class ComplianceSiteViewSerializer(serializers.ModelSerializer):
    site = AddressSerializer(source="site.address")
    licences = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=OrganisationDetailSerializer
    )

    class Meta:
        model = ComplianceSiteCase
        fields = ("site", "licences", "status", "organisation")

    def get_licences(self, instance):
        licences = Case.objects.filter(
            baseapplication__application_sites__site__compliance__id=instance.id
        ) | Case.objects.filter(
            baseapplication__application_sites__site__site_records_located_at__compliance__id=instance.id
        )

        return [{"case_id": licence.id, "case_reference": licence.reference_code,} for licence in licences]

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None
