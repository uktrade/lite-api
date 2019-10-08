from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cases.enums import CaseType
from letter_templates.models import LetterTemplate
from picklists.models import PicklistItem


class LetterTemplateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=20,
                                 trim_whitespace=True,
                                 validators=[UniqueValidator(queryset=LetterTemplate.objects.all(), lookup='iexact',
                                                             message='The name of your letter template has to be unique')],
                                 error_messages={'blank': 'Enter a name for the letter template'})
    letter_paragraphs = serializers.PrimaryKeyRelatedField(queryset=PicklistItem.objects.all(),
                                                           many=True)

    def validate_letter_paragraphs(self, attrs):
        if len(attrs) == 0:
            raise serializers.ValidationError('You\'ll need to add at least one letter paragraph')
        return attrs

    class Meta:
        model = LetterTemplate
        fields = '__all__'

    def to_representation(self, value):
        """
        Only show 'application' if it has an application inside,
        and only show 'query' if it has a CLC query inside
        """
        repr_dict = super(LetterTemplateSerializer, self).to_representation(value)
        repr_dict['restricted_to'] = [{'key': x, 'value': CaseType.get_text(x)} for x in
                                      repr_dict['restricted_to'].split(',')]

        return repr_dict
