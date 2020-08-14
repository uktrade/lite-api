from rest_framework import serializers
from rest_framework.fields import UUIDField
from rest_framework.relations import PrimaryKeyRelatedField

from api.conf.serializers import PrimaryKeyRelatedSerializerField
from gov_users.enums import GovUserStatuses
from lite_content.lite_api import strings
from api.organisations.models import Organisation
from api.queues.constants import SYSTEM_QUEUES
from api.queues.models import Queue
from api.queues.serializers import TinyQueueSerializer
from static.statuses.models import CaseStatus
from static.statuses.serializers import CaseStatusSerializer
from api.teams.models import Team
from api.teams.serializers import TeamSerializer, TeamReadOnlySerializer
from api.users.enums import UserType
from api.users.models import GovUser
from api.users.models import Role, Permission


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
    type = serializers.ChoiceField(choices=UserType.non_system_choices())
    name = serializers.CharField(max_length=30, error_messages={"blank": strings.Roles.BLANK_NAME},)
    statuses = PrimaryKeyRelatedSerializerField(
        queryset=CaseStatus.objects.all(), many=True, required=False, serializer=CaseStatusSerializer
    )

    class Meta:
        model = Role
        fields = (
            "id",
            "name",
            "permissions",
            "type",
            "organisation",
            "statuses",
        )


class RoleListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    permissions = PrimaryKeyRelatedField(many=True, read_only=True)


class RoleListStatusesSerializer(RoleListSerializer):
    statuses = PrimaryKeyRelatedSerializerField(
        queryset=CaseStatus.objects.all(), many=True, required=False, serializer=CaseStatusSerializer
    )


class GovUserListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    status = serializers.ChoiceField(choices=GovUserStatuses.choices)
    team = TeamReadOnlySerializer()
    role_name = serializers.CharField(source="role.name")


class GovUserViewSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    role = RoleListStatusesSerializer()
    default_queue = serializers.SerializerMethodField()

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
            "default_queue",
        )

    def get_default_queue(self, instance):
        queue_id = str(instance.default_queue)

        if queue_id in SYSTEM_QUEUES.keys():
            return {"id": queue_id, "name": SYSTEM_QUEUES[queue_id]}
        else:
            return TinyQueueSerializer(Queue.objects.get(pk=queue_id)).data


class GovUserCreateOrUpdateSerializer(GovUserViewSerializer):
    status = serializers.ChoiceField(choices=GovUserStatuses.choices, default=GovUserStatuses.ACTIVE)
    email = serializers.EmailField(
        error_messages={"blank": strings.Users.INVALID_EMAIL, "invalid": strings.Users.INVALID_EMAIL},
    )
    team = PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        error_messages={"null": strings.Users.NULL_TEAM, "invalid": strings.Users.NULL_TEAM},
    )
    role = PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        error_messages={"null": strings.Users.NULL_ROLE, "invalid": strings.Users.NULL_ROLE},
    )
    default_queue = UUIDField(
        error_messages={"null": strings.Users.NULL_DEFAULT_QUEUE, "invalid": strings.Users.NULL_DEFAULT_QUEUE},
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
            "default_queue",
        )

    def __init__(self, *args, **kwargs):
        self.is_creating = kwargs.pop("is_creating", True)
        super(GovUserCreateOrUpdateSerializer, self).__init__(*args, **kwargs)

    def validate(self, data):
        validated_data = super().validate(data)
        email = data.get("email")

        if email and (self.is_creating or email.lower() != self.instance.email.lower()):
            if GovUser.objects.filter(email__iexact=data.get("email")).exists():
                raise serializers.ValidationError({"email": [strings.Users.UNIQUE_EMAIL]})

        default_queue = str(validated_data.get("default_queue") or self.instance.default_queue)
        team = validated_data.get("team") or self.instance.team

        is_system_queue = default_queue in SYSTEM_QUEUES.keys()
        is_work_queue = Queue.objects.filter(id=default_queue).exists()

        if not is_system_queue and not is_work_queue:
            raise serializers.ValidationError({"default_queue": [strings.Users.NULL_DEFAULT_QUEUE]})

        if is_work_queue and not Queue.objects.values_list("team_id", flat=True).get(id=default_queue) == team.id:
            raise serializers.ValidationError({"default_queue": [strings.Users.INVALID_DEFAULT_QUEUE % team.name]})

        return validated_data


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
