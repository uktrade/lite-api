from rest_framework import serializers

from api.core.tests.models import ChildModel


class ChildModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildModel
        fields = (
            "id",
            "name",
        )
