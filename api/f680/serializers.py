from rest_framework import serializers
from rest_framework.fields import CharField

from api.applications.mixins.serializers import PartiesSerializerMixin
from api.applications.serializers.generic_application import GenericApplicationViewSerializer
from .models import F680Application  # /PS-IGNORE


class F680Serializer(serializers.ModelSerializer):  # /PS-IGNORE
    class Meta:
        model = F680Application  # /PS-IGNORE
        fields = ["id", "data", "name", "status"]

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        return super().create(validated_data)


class F680ApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    data = serializers.JSONField()

    class Meta:
        model = F680Application
        fields = GenericApplicationViewSerializer.Meta.fields + PartiesSerializerMixin.Meta.fields + ("data",)


class F680ApplicationUpdateSerializer(serializers.ModelSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": "Enter a reference name for the application"},
    )

    class Meta:
        model = F680Application
        fields = (
            "name",
            "data",
            "status",
        )

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.name = validated_data.get("name", instance.name)
        instance.data = validated_data.get("data", instance.data)
        # instance.status = validated_data.get("status", instance.status)
        # instance.clearance_level = validated_data.get("clearance_level", instance.clearance_level)

        instance = super().update(instance, validated_data)
        return instance
