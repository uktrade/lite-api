from rest_framework import serializers

from letter_templates.models import LetterLayout


class LetterLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterLayout
        fields = ["id", "filename", "name"]
