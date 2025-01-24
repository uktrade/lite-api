from rest_framework import serializers

from api.applications.serializers.fields import CaseStatusField
from api.organisations.serializers import OrganisationDetailSerializer

from api.f680.models import F680Application  # /PS-IGNORE


class F680Serializer(serializers.ModelSerializer):  # /PS-IGNORE
    status = CaseStatusField(read_only=True)
    organisation = OrganisationDetailSerializer(read_only=True)

    class Meta:
        model = F680Application  # /PS-IGNORE
        fields = [
            "id",
            "application",
            "status",
            "reference_code",
            "organisation",
        ]

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        return super().create(validated_data)
