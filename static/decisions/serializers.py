from rest_framework import serializers

from api.conf.serializers import KeyValueChoiceField
from cases.enums import AdviceType
from static.decisions.models import Decision


class DecisionSerializer(serializers.ModelSerializer):
    name = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = Decision
        fields = (
            "id",
            "name",
        )
