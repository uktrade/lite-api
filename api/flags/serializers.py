from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from api.core.serializers import PrimaryKeyRelatedSerializerField
from api.flags.enums import FlagLevels, FlagStatuses, FlagColours
from api.flags.models import Flag, FlaggingRule
from lite_content.lite_api import strings
from api.teams.models import Team
from api.teams.serializers import TeamSerializer, TeamReadOnlySerializer


class FlagReadOnlySerializer(serializers.Serializer):
    """
    More performant read_only flag serializer
    """

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    colour = serializers.CharField(read_only=True)
    level = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    priority = serializers.IntegerField(read_only=True)
    blocks_approval = serializers.BooleanField(read_only=True)
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamReadOnlySerializer)


class FlaggingRuleReadOnlySerializer(serializers.Serializer):
    level = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    matching_values = serializers.ListField()
    matching_groups = serializers.ListField()


class FlagwithFlaggingRulesReadOnlySerializer(FlagReadOnlySerializer):
    flagging_rules = FlaggingRuleReadOnlySerializer(many=True, read_only=True)


class FlagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=25,
        validators=[UniqueValidator(queryset=Flag.objects.all(), lookup="iexact", message=strings.Flags.NON_UNIQUE)],
        error_messages={"blank": strings.Flags.BLANK_NAME},
    )
    colour = serializers.ChoiceField(choices=FlagColours.choices, default=FlagColours.DEFAULT)
    level = serializers.ChoiceField(
        choices=FlagLevels.choices, error_messages={"invalid_choice": "Select a parameter"},
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
    blocks_approval = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={"required": strings.Flags.ValidationErrors.BLOCKING_APPROVAL_MISSING,},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.context and not self.context.get("request").method == "GET":
            self.initial_data["team"] = self.context.get("request").user.govuser.team_id

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
            "blocks_approval",
        )

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.label = validated_data.get("label", instance.label)
        instance.colour = validated_data.get("colour", instance.colour)
        instance.priority = validated_data.get("priority", instance.priority)
        instance.status = validated_data.get("status", instance.status)
        instance.blocks_approval = validated_data.get("blocks_approval", instance.blocks_approval)
        instance.save()
        return instance


class FlagAssignmentSerializer(serializers.Serializer):
    flags = serializers.PrimaryKeyRelatedField(queryset=Flag.objects.all(), many=True)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_flags(self, flags):
        team_flags = list(
            Flag.objects.filter(level=self.context["level"], team=self.context["team"], status=FlagStatuses.ACTIVE,)
        )

        if not set(flags).issubset(list(team_flags)):
            raise serializers.ValidationError("You can only assign flags that are available to your team.")

        return flags


class CaseListFlagSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField()
    colour = serializers.CharField()
    priority = serializers.IntegerField()
    level = serializers.CharField()


class FlaggingRuleSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)
    level = serializers.ChoiceField(
        choices=FlagLevels.choices, error_messages={"required": "Select a parameter", "null": "Select a parameter",},
    )
    status = serializers.ChoiceField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE)
    flag = PrimaryKeyRelatedField(queryset=Flag.objects.all(), error_messages={"null": strings.FlaggingRules.NO_FLAG})
    matching_values = serializers.ListField(child=serializers.CharField(), required=False)
    matching_groups = serializers.ListField(child=serializers.CharField(), required=False)
    is_for_verified_goods_only = serializers.BooleanField(required=False, allow_null=True)

    class Meta:
        model = FlaggingRule
        fields = (
            "id",
            "team",
            "level",
            "flag",
            "status",
            "matching_values",
            "matching_groups",
            "is_for_verified_goods_only",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, "initial_data"):
            if "level" not in self.initial_data:
                self.initial_data["level"] = self.instance.level if self.instance else None
            if "matching_values" not in self.initial_data:
                self.initial_data["matching_values"] = self.instance.matching_values if self.instance else []
            if "matching_groups" not in self.initial_data:
                self.initial_data["matching_groups"] = self.instance.matching_groups if self.instance else []
            if "is_for_verified_goods_only" not in self.initial_data:
                self.initial_data["is_for_verified_goods_only"] = (
                    self.instance.is_for_verified_goods_only if self.instance else None
                )

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        instance.matching_values = validated_data.get("matching_values", instance.matching_values)
        instance.matching_groups = validated_data.get("matching_groups", instance.matching_groups)
        instance.flag = validated_data.get("flag", instance.flag)
        instance.is_for_verified_goods_only = validated_data.get(
            "is_for_verified_goods_only", instance.is_for_verified_goods_only
        )
        instance.save()
        return instance

    def validate(self, data):
        errors = {}
        validated_data = super().validate(data)

        matching_values = validated_data.get("matching_values")
        matching_groups = validated_data.get("matching_groups")

        if validated_data["level"] == FlagLevels.GOOD:
            if not matching_values and not matching_groups:
                errors["matching_values"] = "Enter a control list entry"
                errors["matching_groups"] = "Enter a control list entry"
        elif validated_data["level"] == FlagLevels.DESTINATION:
            if not matching_values:
                errors["matching_values"] = "Enter a destination"
        elif validated_data["level"] == FlagLevels.CASE:
            if not matching_values:
                errors["matching_values"] = "Enter an application type"

        if (
            "level" in validated_data
            and validated_data["level"] == FlagLevels.GOOD
            and validated_data["is_for_verified_goods_only"] is None
        ):
            errors["is_for_verified_goods_only"] = strings.FlaggingRules.NO_ANSWER_VERIFIED_ONLY

        if errors:
            raise serializers.ValidationError(errors)

        return validated_data


class FlaggingRuleListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    team = TeamReadOnlySerializer()
    level = serializers.ChoiceField(choices=FlagLevels.choices)
    status = serializers.ChoiceField(choices=FlagStatuses.choices)
    flag = PrimaryKeyRelatedField(queryset=Flag.objects.all())
    flag_name = serializers.CharField(source="flag.name")
    matching_values = serializers.ListField(child=serializers.CharField())
    matching_groups = serializers.ListField(child=serializers.CharField())
