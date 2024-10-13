from rest_framework import serializers

from api.core.serializers import PrimaryKeyRelatedSerializerField
from api.flags.enums import (
    FlagPermissions,
    FlagStatuses,
)
from api.flags.models import Flag
from api.teams.models import Team
from api.teams.serializers import TeamReadOnlySerializer


class FlagSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamReadOnlySerializer)

    class Meta:
        model = Flag
        fields = (
            "id",
            "name",
            "alias",
            "colour",
            "level",
            "label",
            "status",
            "priority",
            "blocks_finalising",
            "removable_by",
            "team",
        )


class FlagAssignmentSerializer(serializers.Serializer):
    flags = serializers.PrimaryKeyRelatedField(queryset=Flag.objects.all(), many=True)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_flags(self, flags):
        level, team, user, obj = self.context["level"], self.context["team"], self.context["user"], self.context["obj"]

        previously_assigned_team_flags = obj.flags.filter(level=level, team=team)
        previously_assigned_deactivated_team_flags = obj.flags.filter(
            level=level, team=user.team, status=FlagStatuses.DEACTIVATED
        )

        ignored_flags = flags + [x for x in previously_assigned_deactivated_team_flags]

        removed_flags = [flag for flag in previously_assigned_team_flags if flag not in ignored_flags]

        user_permissions = [p.name for p in user.role.permissions.all()]

        cannot_remove_some_flags = any(
            [
                flag.removable_by != FlagPermissions.DEFAULT
                and FlagPermissions.PERMISSIONS_MAPPING[flag.removable_by].value not in user_permissions
                for flag in removed_flags
            ]
        )

        if cannot_remove_some_flags:
            flags_user_cannot_remove = []

            for flag in removed_flags:
                if (
                    flag.removable_by != FlagPermissions.DEFAULT
                    and FlagPermissions.PERMISSIONS_MAPPING[flag.removable_by].value not in user_permissions
                ):
                    flags_user_cannot_remove.append(flag.name)

            flags_list = ", ".join(flags_user_cannot_remove)

            raise serializers.ValidationError(f"You do not have permission to remove the following flags: {flags_list}")

        team_flags = list(
            Flag.objects.filter(
                level=level,
                team=team,
                status=FlagStatuses.ACTIVE,
            )
        )

        if not set(flags).issubset(list(team_flags)):
            raise serializers.ValidationError("You can only assign flags that are available to your team.")

        return flags


class CaseListFlagSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    alias = serializers.CharField()
    label = serializers.CharField()
    colour = serializers.CharField()
    priority = serializers.IntegerField()
    level = serializers.CharField()
