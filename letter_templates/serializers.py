from rest_framework import serializers

from letter_templates.models import LetterTemplate


class LetterTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterTemplate
        fields = '__all__'
