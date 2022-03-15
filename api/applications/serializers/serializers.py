from rest_framework import serializers

from api.applications.models import PartyOnApplication
from api.parties.serializers import PartySerializer


class PartyOnApplicationSerializer(serializers.ModelSerializer):
    party = PartySerializer()

    class Meta:
        fields = ("party",)
        model = PartyOnApplication
