from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from conf.serializers import PrimaryKeyRelatedSerializerField
from flags.enums import FlagLevels, FlagStatuses, FlagColours
from flags.models import Flag, FlaggingRule
from lite_content.lite_api import strings
from teams.models import Team
from teams.serializers import TeamSerializer


class FlagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=25,
        validators=[UniqueValidator(queryset=Flag.objects.all(), lookup="iexact", message=strings.Flags.NON_UNIQUE)],
        error_messages={"blank": strings.Flags.BLANK_NAME},
    )
    colour = serializers.ChoiceField(choices=FlagColours.choices, default=FlagColours.DEFAULT)
    level = serializers.ChoiceField(
        choices=FlagLevels.choices, error_messages={"invalid_choice": strings.Flags.BLANK_LEVEL},
    )
    label = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
        error_messages={"blank": strings.Flags.ValidationErrors.LABEL_MISSING,},
    )
    status = serializers.ChoiceField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE)
    priority = serializers.IntegerField(
        default=0,
        min_value=0,
        max_value=100,
        error_messages={
            "invalid": strings.Flags.ValidationErrors.PRIORITY,
            "max_value": strings.Flags.ValidationErrors.PRIORITY_TOO_LARGE,
            "min_value": strings.Flags.ValidationErrors.PRIORITY_NEGATIVE,
        },
    )
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.context and not self.context.get("request").method == "GET":
            self.initial_data["team"] = self.context.get("request").user.team_id

        if hasattr(self, "initial_data"):
            if self.initial_data.get("colour") != FlagColours.DEFAULT:
                self.fields["label"].required = True
                self.fields["label"].allow_blank = False

    class Meta:
        model = Flag
        fields = (
            "id",
            "name",
            "level",
            "team",
            "status",
            "label",
            "colour",
            "priority",
        )

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.label = validated_data.get("label", instance.label)
        instance.colour = validated_data.get("colour", instance.colour)
        instance.priority = validated_data.get("priority", instance.priority)
        instance.status = validated_data.get("status", instance.status)
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
        fields = ("name", "team", "colour", "label", "priority")


class FlaggingRuleSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)
    level = serializers.ChoiceField(
        choices=FlagLevels.choices, error_messages={"required": strings.Flags.BLANK_LEVEL,},
    )
    status = serializers.ChoiceField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE)
    flag = PrimaryKeyRelatedField(queryset=Flag.objects.all(), error_messages={"null": strings.FlaggingRules.NO_FLAG})
    flag_name = serializers.SerializerMethodField()
    matching_value = serializers.CharField(
        max_length=100, error_messages={"blank": strings.FlaggingRules.NO_MATCHING_VALUE}
    )
    is_for_verified_goods_only = serializers.BooleanField(required=False)

    def get_flag_name(self, instance):
        return instance.flag.name

    class Meta:
        model = FlaggingRule
        fields = (
            "id",
            "team",
            "level",
            "flag",
            "flag_name",
            "status",
            "matching_value",
            "is_for_verified_goods_only",
        )
        validators = [
            UniqueTogetherValidator(
                queryset=FlaggingRule.objects.all(),
                fields=["level", "flag", "matching_value"],
                message=strings.FlaggingRules.DUPLICATE_RULE,
            )
        ]

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        instance.matching_value = validated_data.get("matching_value", instance.matching_value)
        instance.flag = validated_data.get("flag", instance.flag)
        instance.is_for_verified_goods_only = validated_data.get(
            "is_for_verified_goods_only", instance.is_for_verified_goods_only
        )
        instance.save()
        return instance

    def validate(self, data):
        if "level" in data and data["level"] == "Good" and "is_for_verified_goods_only" not in data:
            raise serializers.ValidationError(
                {"is_for_verified_goods_only": strings.FlaggingRules.NO_ANSWER_VERIFIED_ONLY}
            )
        return super().validate(data)
