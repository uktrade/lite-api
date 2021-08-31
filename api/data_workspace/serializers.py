from api.cases.models import EcjuQuery

from rest_framework import serializers


class EcjuQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = EcjuQuery
        fields = "__all__"
