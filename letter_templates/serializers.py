from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cases.enums import CaseType
from conf.serializers import CommaSeparatedListField, PrimaryKeyRelatedSerializerField
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
    restricted_to = CommaSeparatedListField(error_messages={'required': 'Select which types of case this letter template can apply to'},
                                            required=True,
                                            allow_blank=False,
                                            allow_null=False)
    layout = PrimaryKeyRelatedSerializerField(queryset=LetterLayout.objects.all(),
                                              serializer=LetterLayoutSerializer,
                                              error_messages={'required': 'Select the layout you want to use for this letter template'})

    @staticmethod
    def validate_restricted_to(self, attrs):
        if not attrs:
            raise serializers.ValidationError('Select at least one case restriction for your letter template')
        return attrs

    @staticmethod
    def validate_letter_paragraphs(self, attrs):
        if not attrs:
            raise serializers.ValidationError('You\'ll need to add at least one letter paragraph')
        return attrs

    class Meta:
        model = LetterTemplate
        fields = '__all__'

    def to_representation(self, value):
        """
        Convert restricted_to to list of key value entries
        """
        repr_dict = super(LetterTemplateSerializer, self).to_representation(value)

        repr_dict['restricted_to'] = [{'key': x, 'value': CaseType.get_text(x)} for x in
                                      repr_dict['restricted_to']]
        repr_dict['restricted_to'].sort(key=lambda x: x['value'])

        return repr_dict
