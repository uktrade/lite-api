from rest_framework import serializers

from api.core.serializers import KeyValueChoiceField
from api.cases.enums import AdviceType
from api.static.decisions.models import Decision


class DecisionSerializer(serializers.ModelSerializer):
    name = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = Decision
        fields = (
            "id",
            "name",
        )
