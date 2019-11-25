from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from content_strings.strings import get_string
from gov_users.enums import GovUserStatuses
from organisations.models import Organisation
from teams.models import Team
from teams.serializers import TeamSerializer
from users.enums import UserType
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
    permissions = PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True, required=False)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False, allow_null=True)
    type = serializers.ChoiceField(
        choices=UserType.choices
    )
    name = serializers.CharField(
        max_length=30,
        error_messages={"blank": get_string("roles.blank_name")},
    )

    class Meta:
        model = Role
        fields = (
            "id",
            "name",
            "permissions",
            "type",
            "organisation"
        )


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
        error_messages={"blank": get_string("users.invalid_email"), "invalid": get_string("users.invalid_email"), },
    )
    team = PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        error_messages={"null": get_string("users.null_team"), "invalid": get_string("users.null_team"), },
    )
    role = PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        error_messages={"null": get_string("users.null_role"), "invalid": get_string("users.null_role"), },
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
