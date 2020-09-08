from rest_framework import serializers
from rest_framework.fields import UUIDField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.utils import model_meta

from api.core.serializers import PrimaryKeyRelatedSerializerField
from api.gov_users.enums import GovUserStatuses
from lite_content.lite_api import strings
from api.organisations.models import Organisation
from api.queues.constants import SYSTEM_QUEUES
from api.queues.models import Queue
from api.queues.serializers import TinyQueueSerializer
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.statuses.serializers import CaseStatusSerializer
from api.teams.models import Team
from api.teams.serializers import TeamSerializer, TeamReadOnlySerializer
from api.users.enums import UserType
from api.users.models import GovUser, BaseUser
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
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    status = serializers.ChoiceField(choices=GovUserStatuses.choices)
    team = TeamReadOnlySerializer()
    role_name = serializers.CharField(source="role.name")


class GovUserViewSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
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

    # from baseuser
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")

    email = serializers.EmailField(
        error_messages={"blank": strings.Users.INVALID_EMAIL, "invalid": strings.Users.INVALID_EMAIL},
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    # from model
    status = serializers.ChoiceField(choices=GovUserStatuses.choices, default=GovUserStatuses.ACTIVE)
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
            if GovUser.objects.filter(baseuser_ptr__email__iexact=data.get("email")).exists():
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

    def create(self, validated_data):
        base_user_defaults = {
            "email": validated_data.pop("email"),
            "last_name": validated_data.pop("last_name", None),
            "first_name": validated_data.pop("first_name", None),
        }
        base_user, _ = BaseUser.objects.get_or_create(
            email__iexact=base_user_defaults["email"], type=UserType.INTERNAL, defaults=base_user_defaults
        )
        instance = GovUser.objects.create(baseuser_ptr=base_user, **validated_data)
        return instance

    def update(self, instance, validated_data):
        info = model_meta.get_field_info(instance)
        baseuser_info = model_meta.get_field_info(instance.baseuser_ptr)

        baseuser_dirty = False
        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.

        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            elif attr in baseuser_info.fields:
                setattr(instance.baseuser_ptr, attr, value)
                baseuser_dirty = True
            else:
                setattr(instance, attr, value)

        if baseuser_dirty:
            instance.baseuser_ptr.save()
        instance.save()

        # Note that many-to-many fields are set after updating instance.
        # Setting m2m fields triggers signals which could potentially change
        # updated instance and we do not want it to collide with .update()
        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        return instance


class GovUserSimpleSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")
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
