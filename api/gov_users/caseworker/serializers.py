from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.utils import model_meta

from api.gov_users.enums import GovUserStatuses
from api.gov_users.serializers import RoleListStatusesSerializer
from api.queues.constants import SYSTEM_QUEUES
from api.queues.models import Queue
from api.teams.models import Team
from api.teams.serializers import TeamSerializer
from api.users.models import GovUser, Role


class GovUserUpdateSerializer(serializers.ModelSerializer):

    # from baseuser
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")

    team = PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
    )
    role = PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
    )

    email = serializers.EmailField()

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

    def validate_email(self, value):
        value = value.lower()
        if value != self.instance.email:
            if GovUser.objects.filter(baseuser_ptr__email__iexact=value).exists():
                raise serializers.ValidationError({"email": ["This email has already been registered"]})
        return value

    def validate_default_queue(self, value):
        default_queue = value or self.instance.default_queue
        team = self.initial_data.get("team") or self.instance.team_id
        is_system_queue = str(default_queue) in SYSTEM_QUEUES.keys()
        if not is_system_queue:
            try:
                queue = Queue.objects.get(id=default_queue)
                if str(queue.team_id) != team:
                    raise serializers.ValidationError("select a valid queue for team")
            except Queue.DoesNotExist:
                raise serializers.ValidationError("select a valid queue")

        return default_queue

    def update(self, instance, validated_data):

        baseuser_info = model_meta.get_field_info(instance.baseuser_ptr)
        baseuser_dirty = False

        for attr, value in validated_data.items():
            if attr in baseuser_info.fields:
                setattr(instance.baseuser_ptr, attr, value)
                baseuser_dirty = True
            else:
                setattr(instance, attr, value)

        if baseuser_dirty:
            instance.baseuser_ptr.save()

        if "status" in validated_data.keys() and validated_data["status"] == GovUserStatuses.DEACTIVATED:
            # user is being deactivate remove all assigned cases.
            instance.unassign_from_cases()

        instance.save()
        return instance


class GovUserViewSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")
    team = TeamSerializer()
    role = RoleListStatusesSerializer()

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
        extra_kwargs = {"first_name": {"read_only": True}, "last_name": {"read_only": True}}


class GovUserListSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")

    class Meta:
        model = GovUser
        fields = (
            "id",
            "email",
        )
