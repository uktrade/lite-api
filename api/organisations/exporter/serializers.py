from rest_framework import serializers

from api.organisations.models import Organisation


class RelatedOrganisationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organisation
        fields = [
            "id",
            "name",
            "type",
            "status",
        ]
