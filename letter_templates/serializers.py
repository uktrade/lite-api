from rest_framework import serializers

from letter_templates.models import LetterTemplate
from picklists.models import PicklistItem


class LetterTemplateSerializer(serializers.ModelSerializer):
    letter_paragraphs = serializers.PrimaryKeyRelatedField(queryset=PicklistItem.objects.all(),
                                                           many=True)

    class Meta:
        model = LetterTemplate
        fields = '__all__'
