from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.cases.models import CaseType
from api.cases.serializers import CaseTypeSerializer, CaseTypeReferenceListSerializer
from api.core.serializers import PrimaryKeyRelatedSerializerField
from api.letter_templates.models import LetterTemplate
from lite_content.lite_api import strings
from api.picklists.models import PicklistItem
from api.staticdata.decisions.models import Decision
from api.staticdata.decisions.serializers import DecisionSerializer
from api.staticdata.letter_layouts.models import LetterLayout
from api.staticdata.letter_layouts.serializers import LetterLayoutSerializer, LetterLayoutReadOnlySerializer


class LetterTemplateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=35,
        validators=[
            UniqueValidator(
                queryset=LetterTemplate.objects.all(),
                lookup="iexact",
                message=strings.LetterTemplates.UNIQUE_NAME,
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
    decisions = PrimaryKeyRelatedSerializerField(
        queryset=Decision.objects.all(), serializer=DecisionSerializer, required=False, many=True
    )
    visible_to_exporter = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"required": strings.LetterTemplates.VISIBLE_TO_EXPORTER},
    )
    include_digital_signature = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"required": strings.LetterTemplates.INCLUDE_DIGITAL_SIGNATURE},
    )

    class Meta:
        model = LetterTemplate
        fields = "__all__"

    @staticmethod
    def validate_case_types(attrs):
        if not attrs:
            raise serializers.ValidationError(strings.LetterTemplates.NEED_AT_LEAST_ONE_CASE_TYPE)
        return attrs


class LetterTemplateListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    case_types = CaseTypeReferenceListSerializer(many=True)
    layout = LetterLayoutReadOnlySerializer()
    updated_at = serializers.DateTimeField()
