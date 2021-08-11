from rest_framework import serializers

from api.applications.models import PartyOnApplication


class PartyOnApplicationViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyOnApplication
        fields = "__all__"
