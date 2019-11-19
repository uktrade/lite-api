from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from conf.constants import Permissions
from content_strings.strings import get_string
from gov_users.enums import GovUserStatuses
from teams.models import Team
from teams.serializers import TeamSerializer
from users.models import GovUser
from users.models import Role, Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = (
            "id",
            "name",
        )


class RoleSerializer(serializers.ModelSerializer):
    permissions = PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True)
    name = serializers.CharField(
        max_length=30,
        validators=[
            UniqueValidator(queryset=Role.objects.all(), lookup="iexact", message=get_string("roles.duplicate_name"),)
        ],
        error_messages={"blank": get_string("roles.blank_name")},
    )

    class Meta:
        model = Role
        fields = (
            "id",
            "name",
            "permissions",
        )

    def update(self, instance, validated_data):
        new_permissions = [permission.id for permission in validated_data["permissions"]]
        confirm_own_advice = Permissions.CONFIRM_OWN_ADVICE in new_permissions
        manage_team_advice = Permissions.MANAGE_TEAM_ADVICE in new_permissions

        # If the request contains the `confirm own advice` permission without the `manage team advice` permission
        if confirm_own_advice and not manage_team_advice:
            previous_permissions = instance.permissions.all().values_list("id", flat=True)

            if Permissions.CONFIRM_OWN_ADVICE in previous_permissions:
                # If `manage team advice` was not sent with the request
                # and `confirm own advice` is in previously set permissions
                # then the request was made to remove the `manage team advice` permission
                new_permissions.remove(Permissions.CONFIRM_OWN_ADVICE)
            else:
                # If `manage team advice` was not sent with the request
                # and `confirm own advice` is not in previously set permissions
                # then the request was made to add the `confirm own advice` permission
                new_permissions.append(Permissions.MANAGE_TEAM_ADVICE)

        validated_data["permissions"] = new_permissions
        return super(RoleSerializer, self).update(instance, validated_data)


class GovUserViewSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    role = RoleSerializer()

    class Meta:
        model = GovUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "status",
            "team",
            "role",
        )


class GovUserCreateSerializer(GovUserViewSerializer):
    status = serializers.ChoiceField(choices=GovUserStatuses.choices, default=GovUserStatuses.ACTIVE)
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=GovUser.objects.all())],
        error_messages={"blank": get_string("users.invalid_email"), "invalid": get_string("users.invalid_email"),},
    )
    team = PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        error_messages={"null": get_string("users.null_team"), "invalid": get_string("users.null_team"),},
    )
    role = PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        error_messages={"null": get_string("users.null_role"), "invalid": get_string("users.null_role"),},
    )

    class Meta:
        model = GovUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "status",
            "team",
            "role",
        )


class GovUserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovUser
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
        )
