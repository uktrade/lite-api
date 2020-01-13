from lite_content.lite_api import strings
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from gov_users.enums import GovUserStatuses
from organisations.models import Organisation
from teams.models import Team
from teams.serializers import TeamSerializer
from users.enums import UserType
from users.models import GovUser, GovNotification
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
    type = serializers.ChoiceField(choices=UserType.choices)
    name = serializers.CharField(max_length=30, error_messages={"blank": strings.Roles.BLANK_NAME},)

    class Meta:
        model = Role
        fields = ("id", "name", "permissions", "type", "organisation")


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
        error_messages={"blank": strings.Users.INVALID_EMAIL, "invalid": strings.Users.INVALID_EMAIL,},
    )
    team = PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        error_messages={"null": strings.Users.NULL_TEAM, "invalid": strings.Users.NULL_TEAM,},
    )
    role = PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        error_messages={"null": strings.Users.NULL_ROLE, "invalid": strings.Users.NULL_ROLE,},
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
    team = serializers.SerializerMethodField()

    class Meta:
        model = GovUser
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "team",
        )

    def get_team(self, instance):
        return instance.team.name


class GovUserNotificationSerializer(serializers.ModelSerializer):
    audit_id = serializers.SerializerMethodField()

    class Meta:
        model = GovNotification
        fields = ("audit_id",)

    def get_audit_id(self, obj):
        return obj.object_id
