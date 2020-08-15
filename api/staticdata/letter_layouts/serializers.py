from rest_framework import serializers

from api.letter_templates.models import LetterLayout


class LetterLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterLayout
        fields = (
            "id",
            "filename",
            "name",
        )


class LetterLayoutReadOnlySerializer(serializers.Serializer):
    filename = serializers.CharField()
    name = serializers.CharField()
