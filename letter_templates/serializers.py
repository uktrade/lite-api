from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cases.enums import CaseType
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

    restricted_to = serializers.ListField(
        child=serializers.CharField(),
        error_messages={"required": "Select which types of case this letter template can apply to",},
    )
    restricted_to_display = serializers.SerializerMethodField()

    layout = PrimaryKeyRelatedSerializerField(
        queryset=LetterLayout.objects.all(),
        serializer=LetterLayoutSerializer,
        error_messages={"required": "Select the layout you want to use for this letter template"},
    )

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

    def get_restricted_to_display(self, instance):
        """
        Provide display values for restricted_to.
        """
        display_names = dict(CaseType.choices)
        return [display_names.get(restricted_to) for restricted_to in instance.restricted_to]

    class Meta:
        model = LetterTemplate
        fields = "__all__"
