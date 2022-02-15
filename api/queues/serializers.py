from rest_framework import serializers

from lite_content.lite_api import strings
from api.queues.constants import SYSTEM_QUEUES
from api.queues.models import Queue
from api.teams.models import Team
from api.teams.serializers import TeamReadOnlySerializer


class CasesQueueViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = (
            "id",
            "name",
        )


class QueueViewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    is_system_queue = serializers.SerializerMethodField()
    countersigning_queue = serializers.SerializerMethodField()

    def get_countersigning_queue(self, instance):
        if isinstance(instance, Queue):
            return instance.countersigning_queue_id
        else:
            return instance.get("countersigning_queue", None)

    def get_is_system_queue(self, instance):
        if isinstance(instance, dict):
            return instance["id"] in SYSTEM_QUEUES.keys()
        else:
            return instance.id in SYSTEM_QUEUES.keys()


class TinyQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = (
            "id",
            "name",
        )


class QueueListSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    team = TeamReadOnlySerializer(read_only=True)
    countersigning_queue = TinyQueueSerializer(read_only=True)


class QueueCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        error_messages={
            "blank": strings.Queues.BLANK_NAME,
        }
    )
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    countersigning_queue = serializers.PrimaryKeyRelatedField(
        queryset=Queue.objects.all(), required=False, allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["countersigning_queue"].queryset = Queue.objects.exclude(id=self.instance.id)

    class Meta:
        model = Queue
        fields = (
            "id",
            "name",
            "team",
            "countersigning_queue",
        )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=("name", "team"),
                message="Another queue in this team already has this name. Please pick a different name.",
            )
        ]
