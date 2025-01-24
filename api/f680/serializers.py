from rest_framework import serializers

from api.applications.mixins.serializers import PartiesSerializerMixin
from api.applications.serializers.generic_application import GenericApplicationViewSerializer
from .models import F680Application  # /PS-IGNORE


class F680Serializer(serializers.ModelSerializer):  # /PS-IGNORE
    class Meta:
        model = F680Application  # /PS-IGNORE
        fields = ["id", "data", "status"]

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        return super().create(validated_data)


class F680ApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    data = serializers.JSONField()

    class Meta:
        model = F680Application
        fields = GenericApplicationViewSerializer.Meta.fields + PartiesSerializerMixin.Meta.fields + ("data",)
