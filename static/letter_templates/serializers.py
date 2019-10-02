from rest_framework import serializers

from static.letter_templates.models import LetterTemplate


class LetterTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterTemplate
        fields = '__all__'
