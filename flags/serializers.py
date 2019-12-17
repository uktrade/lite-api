from lite_content.lite_api import flags

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from conf.serializers import PrimaryKeyRelatedSerializerField
from flags.enums import FlagLevels, FlagStatuses
from flags.models import Flag
from teams.models import Team
from teams.serializers import TeamSerializer


class FlagSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)
    level = serializers.ChoiceField(
        choices=FlagLevels.choices, error_messages={"invalid_choice": flags.Flags.BLANK_LEVEL},
    )
    status = serializers.ChoiceField(choices=FlagStatuses.choices, default=FlagStatuses.ACTIVE)
    name = serializers.CharField(
        max_length=20,
        trim_whitespace=True,
        validators=[
            UniqueValidator(
                queryset=Flag.objects.all(), lookup="iexact", message=flags.Flags.NON_UNIQUE,
            )
        ],
        error_messages={"blank": flags.Flags.BLANK_NAME},
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
        instance.level = validated_data.get("level", instance.level)
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
