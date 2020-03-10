from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from conf.serializers import PrimaryKeyRelatedSerializerField
from flags.enums import FlagLevels, FlagStatuses
from flags.models import Flag, FlaggingRule
from lite_content.lite_api import strings
from teams.models import Team
from teams.serializers import TeamSerializer


class FlagSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)
    level = serializers.ChoiceField(
        choices=FlagLevels.choices, error_messages={"invalid_choice": strings.Flags.BLANK_LEVEL},
    )
    status = serializers.ChoiceField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE)
    name = serializers.CharField(
        max_length=20,
        trim_whitespace=True,
        validators=[UniqueValidator(queryset=Flag.objects.all(), lookup="iexact", message=strings.Flags.NON_UNIQUE)],
        error_messages={"blank": strings.Flags.BLANK_NAME},
    )

    class Meta:
        model = Flag
        fields = (
            "id",
            "name",
            "level",
            "team",
            "status",
        )

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance


class FlagAssignmentSerializer(serializers.Serializer):
    flags = serializers.PrimaryKeyRelatedField(queryset=Flag.objects.all(), many=True)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_flags(self, flags):
        team_good_level_flags = list(
            Flag.objects.filter(level=self.context["level"], team=self.context["team"], status=FlagStatuses.ACTIVE,)
        )
        if not set(flags).issubset(list(team_good_level_flags)):
            raise serializers.ValidationError("You can only assign case-level flags that are available to your team.")
        return flags


class CaseListFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = (
            "name",
            "team",
        )


class FlaggingRuleSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)
    level = serializers.ChoiceField(
        choices=FlagLevels.choices, error_messages={"invalid_choice": strings.Flags.BLANK_LEVEL},
    )
    status = serializers.ChoiceField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE)
    flag = PrimaryKeyRelatedField(queryset=Flag.objects.all())
    flag_name = serializers.SerializerMethodField()

    def get_flag_name(self, instance):
        return instance.flag.name

    class Meta:
        model = FlaggingRule
        fields = ("id", "team", "level", "flag", "flag_name", "status", "matching_value")
        validators = [
            UniqueTogetherValidator(
                queryset=FlaggingRule.objects.all(),
                fields=["level", "flag", "matching_value"],
                message="This combination already exists",
            )
        ]

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        instance.matching_value = validated_data.get("matching_value", instance.matching_value)
        instance.flag = validated_data.get("flag", instance.flag)
        instance.save()
        return instance
