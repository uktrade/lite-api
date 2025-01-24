from rest_framework import serializers

from api.applications.serializers.fields import CaseStatusField
from api.organisations.serializers import OrganisationDetailSerializer

from api.f680.models import F680Application  # /PS-IGNORE


class F680Serializer(serializers.ModelSerializer):  # /PS-IGNORE
    status = CaseStatusField(read_only=True)
    organisation = OrganisationDetailSerializer(read_only=True)
    name = serializers.SerializerMethodField()
    submitted_at = serializers.DateTimeField(read_only=True)
    submitted_by = serializers.SerializerMethodField()

    class Meta:
        model = F680Application  # /PS-IGNORE
        fields = [
            "id",
            "application",
            "status",
            "sub_status",
            "reference_code",
            "organisation",
            "name",
            "submitted_at",
            "submitted_by",
        ]

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        return super().create(validated_data)

    def get_name(self, application):
        return application.application["application"]["name"]["value"]

    def get_submitted_by(self, application):
        return f"{application.submitted_by.first_name} {application.submitted_by.last_name}"
