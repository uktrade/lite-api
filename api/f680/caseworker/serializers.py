from rest_framework import serializers

from api.applications.serializers.fields import CaseStatusField
from api.organisations.exporter.serializers import RelatedOrganisationSerializer
from api.users.exporter.serializers import RelatedExporterUserSerializer

from api.f680.models import F680Application  # /PS-IGNORE


class F680ApplicationSerializer(serializers.ModelSerializer):  # /PS-IGNORE
    status = CaseStatusField(read_only=True)
    organisation = RelatedOrganisationSerializer(read_only=True)
    submitted_by = RelatedExporterUserSerializer(read_only=True)

    class Meta:
        model = F680Application  # /PS-IGNORE
        fields = [
            "id",
            "application",
            "status",
            "reference_code",
            "organisation",
            "submitted_at",
            "submitted_by",
            "name",
        ]
        read_only_fields = ["id", "status", "reference_code", "organisation", "submitted_at", "submitted_by"]
