from rest_framework import serializers

from api.open_general_licences.serializers import OpenGeneralLicenceSerializer
from api.organisations.serializers import OrganisationDetailSerializer, SiteListSerializer
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum


class OpenGeneralLicenceCaseSerializer(serializers.Serializer):
    organisation = OrganisationDetailSerializer()
    open_general_licence = OpenGeneralLicenceSerializer()
    site = SiteListSerializer()
    status = serializers.SerializerMethodField()

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
