from rest_framework import serializers

from static.case_types.models import CaseType


class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = (
            "id",
            "name",
        )

    def to_representation(self, instance):
        return dict(key=instance.id, value=instance.name)
