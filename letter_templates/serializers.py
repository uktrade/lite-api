from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cases.enums import CaseType
from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from letter_templates.models import LetterTemplate
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout
from static.letter_layouts.serializers import LetterLayoutSerializer


class LetterTemplateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=35,
        validators=[
            UniqueValidator(
                queryset=LetterTemplate.objects.all(),
                lookup="iexact",
                message="The name of your letter template has to be unique",
            )
        ],
        error_messages={"blank": "Enter a name for the letter template"},
    )
    letter_paragraphs = serializers.PrimaryKeyRelatedField(queryset=PicklistItem.objects.all(), many=True)

    restricted_to = serializers.SerializerMethodField()

    layout = PrimaryKeyRelatedSerializerField(
        queryset=LetterLayout.objects.all(),
        serializer=LetterLayoutSerializer,
        error_messages={"required": "Select the layout you want to use for this letter template"},
    )

    class Meta:
        model = LetterTemplate
        fields = "__all__"

    @staticmethod
    def validate_restricted_to(attrs):
        if not attrs:
            raise serializers.ValidationError("Select at least one case restriction for your letter template")
        return attrs

    @staticmethod
    def validate_letter_paragraphs(attrs):
        if not attrs:
            raise serializers.ValidationError("You'll need to add at least one letter paragraph")
        return attrs

    @staticmethod
    def get_restricted_to(instance):
        dicts = []
        case_types = dict(CaseType.choices)
        for value in instance.restricted_to:
            dicts.append(dict(key=value, value=case_types[value]))
        return dicts
