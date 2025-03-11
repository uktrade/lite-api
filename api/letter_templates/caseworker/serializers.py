from rest_framework import serializers

from api.letter_templates.models import LetterTemplate
from api.staticdata.decisions.serializers import DecisionSerializer


class LetterTemplatesSerializer(serializers.ModelSerializer):
    decisions = DecisionSerializer(many=True)

    class Meta:
        model = LetterTemplate
        fields = ("id", "name", "decisions")
