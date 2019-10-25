from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cases.enums import CaseType
from conf.serializers import PrimaryKeyRelatedSerializerField
from letter_templates.models import LetterTemplate
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout
from static.letter_layouts.serializers import LetterLayoutSerializer


class LetterTemplateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=35,
                                 validators=[UniqueValidator(queryset=LetterTemplate.objects.all(), lookup='iexact',
                                                             message='The name of your letter template has to be unique')],
                                 error_messages={'blank': 'Enter a name for the letter template'})
    letter_paragraphs = serializers.PrimaryKeyRelatedField(queryset=PicklistItem.objects.all(),
                                                           many=True)

    # restricted_to is backed by a text field containing comma delimited data.
    restricted_to = serializers.MultipleChoiceField(error_messages={'required': 'Select which types of case this letter template can apply to'},
                                                    required=True,
                                                    allow_blank=False,
                                                    allow_null=False,
                                                    choices=CaseType.choices)
    restricted_to_display = serializers.SerializerMethodField()

    layout = PrimaryKeyRelatedSerializerField(queryset=LetterLayout.objects.all(),
                                              serializer=LetterLayoutSerializer,
                                              error_messages={'required': 'Select the layout you want to use for this letter template'})

    def validate_restricted_to(self, attrs):
        if len(attrs) == 0:
            raise serializers.ValidationError('Select at least one case restriction for your letter template')
        return attrs

    def validate_letter_paragraphs(self, attrs):
        if len(attrs) == 0:
            raise serializers.ValidationError('You\'ll need to add at least one letter paragraph')
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["restricted_to"] = instance.restricted_to.split(",")
        return data

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if "restricted_to" in data:
            data["restricted_to"] = ",".join(data["restricted_to"])

        return data

    def get_restricted_to_display(self, instance):
        """
        Provide display values for restricted_to.
        """
        display_names = dict(CaseType.choices)
        return [display_names.get(r) for r in instance.restricted_to.split(",")]

    class Meta:
        model = LetterTemplate
        fields = '__all__'
