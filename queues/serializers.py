from rest_framework import serializers

from lite_content.lite_api import strings
from queues.constants import SYSTEM_QUEUES
from queues.models import Queue
from teams.models import Team
from teams.serializers import TeamReadOnlySerializer


class CasesQueueViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = ("id", "name")


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
            return instance["id"] in SYSTEM_QUEUES
        else:
            return instance.id in SYSTEM_QUEUES


class QueueListSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    team = TeamReadOnlySerializer(read_only=True)


class TinyQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = (
            "id",
            "name",
        )


class QueueCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages={"blank": strings.Queues.BLANK_NAME,})
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    countersigning_queue = serializers.PrimaryKeyRelatedField(queryset=Queue.objects.all())

    class Meta:
        model = Queue
        fields = (
            "id",
            "name",
            "team",
            "countersigning_queue",
        )
