from rest_framework import serializers

from api.organisations.exporter.serializers import RelatedOrganisationSerializer
from api.users.exporter.serializers import RelatedExporterUserSerializer

from api.f680.models import F680Application  # /PS-IGNORE


class F680ApplicationSerializer(serializers.ModelSerializer):  # /PS-IGNORE
    status = serializers.CharField(source="status__status", read_only=True)
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
        ]
        read_only_fields = ["id", "status", "reference_code", "organisation", "submitted_at", "submitted_by"]

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        validated_data["status"] = self.context["default_status"]
        validated_data["case_type_id"] = self.context["case_type_id"]
        return super().create(validated_data)
