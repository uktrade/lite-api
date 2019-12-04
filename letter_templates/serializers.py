from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from static.case_types.models import CaseType
from static.case_types.serializers import CaseTypeSerializer
from conf.serializers import PrimaryKeyRelatedSerializerField
from letter_templates.models import LetterTemplate
from lite_content.lite_api.letter_templates import LetterTemplatesPage
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout
from static.letter_layouts.serializers import LetterLayoutSerializer


class LetterTemplateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=35,
        validators=[
            UniqueValidator(
                queryset=LetterTemplate.objects.all(), lookup="iexact", message=LetterTemplatesPage.UNIQUE_NAME,
            )
        ],
        error_messages={"blank": LetterTemplatesPage.NAME_REQUIRED},
    )
    letter_paragraphs = serializers.PrimaryKeyRelatedField(queryset=PicklistItem.objects.all(), many=True)

    case_types = PrimaryKeyRelatedSerializerField(
        queryset=CaseType.objects.all(),
        serializer=CaseTypeSerializer,
        error_messages={"required": LetterTemplatesPage.SELECT_THE_CASE_TYPES},
        many=True,
    )

    layout = PrimaryKeyRelatedSerializerField(
        queryset=LetterLayout.objects.all(),
        serializer=LetterLayoutSerializer,
        error_messages={"required": LetterTemplatesPage.SELECT_THE_LAYOUT},
    )

    class Meta:
        model = LetterTemplate
        fields = "__all__"

    @staticmethod
    def validate_case_types(attrs):
        if not attrs:
            raise serializers.ValidationError(LetterTemplatesPage.NEED_AT_LEAST_ONE_CASE_TYPE)
        return attrs

    @staticmethod
    def validate_letter_paragraphs(attrs):
        if not attrs:
            raise serializers.ValidationError(LetterTemplatesPage.NEED_AT_LEAST_ONE_PARAGRAPH)
        return attrs
