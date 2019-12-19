from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cases.models import CaseType
from cases.serializers import CaseTypeSerializer
from conf.serializers import PrimaryKeyRelatedSerializerField
from letter_templates.models import LetterTemplate
from lite_content.lite_api import strings
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout
from static.letter_layouts.serializers import LetterLayoutSerializer


class LetterTemplateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=35,
        validators=[
            UniqueValidator(
                queryset=LetterTemplate.objects.all(), lookup="iexact", message=strings.LetterTemplates.UNIQUE_NAME,
            )
        ],
        error_messages={"blank": strings.LetterTemplates.NAME_REQUIRED},
    )
    letter_paragraphs = serializers.PrimaryKeyRelatedField(queryset=PicklistItem.objects.all(), many=True)

    case_types = PrimaryKeyRelatedSerializerField(
        queryset=CaseType.objects.all(),
        serializer=CaseTypeSerializer,
        error_messages={"required": strings.LetterTemplates.SELECT_THE_CASE_TYPES},
        many=True,
    )

    layout = PrimaryKeyRelatedSerializerField(
        queryset=LetterLayout.objects.all(),
        serializer=LetterLayoutSerializer,
        error_messages={"required": strings.LetterTemplates.SELECT_THE_LAYOUT},
    )

    class Meta:
        model = LetterTemplate
        fields = "__all__"

    @staticmethod
    def validate_case_types(attrs):
        if not attrs:
            raise serializers.ValidationError(strings.LetterTemplates.NEED_AT_LEAST_ONE_CASE_TYPE)
        return attrs

    @staticmethod
    def validate_letter_paragraphs(attrs):
        if not attrs:
            raise serializers.ValidationError(strings.LetterTemplates.NEED_AT_LEAST_ONE_PARAGRAPH)
        return attrs
