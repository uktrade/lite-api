from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cases.models import CaseType
from cases.serializers import CaseTypeSerializer
from conf.serializers import PrimaryKeyRelatedSerializerField
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

    case_types = PrimaryKeyRelatedSerializerField(
        queryset=CaseType.objects.all(),
        serializer=CaseTypeSerializer,
        error_messages={"required": "Select the case types you want to use for this letter template"},
        many=True,
    )

    layout = PrimaryKeyRelatedSerializerField(
        queryset=LetterLayout.objects.all(),
        serializer=LetterLayoutSerializer,
        error_messages={"required": "Select the layout you want to use for this letter template"},
    )

    class Meta:
        model = LetterTemplate
        fields = "__all__"

    @staticmethod
    def validate_case_types(attrs):
        if not attrs:
            raise serializers.ValidationError("You need at least one case type for your letter template")
        return attrs

    @staticmethod
    def validate_letter_paragraphs(attrs):
        if not attrs:
            raise serializers.ValidationError("You need at one letter paragraph for your letter template")
        return attrs
