from rest_framework import serializers

from conf.serializers import KeyValueChoiceField
from static.decisions.enums import DecisionsEnum
from static.decisions.models import Decision


class DecisionSerializer(serializers.ModelSerializer):
    name = KeyValueChoiceField(choices=DecisionsEnum.choices)

    class Meta:
        model = Decision
        fields = ("id", "name",)
