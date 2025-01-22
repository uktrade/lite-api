from rest_framework import serializers

from api.f680.models import F680Application  # /PS-IGNORE


class F680Serializer(serializers.ModelSerializer):  # /PS-IGNORE
    class Meta:
        model = F680Application  # /PS-IGNORE
        fields = ["id", "application", "status"]

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        return super().create(validated_data)
