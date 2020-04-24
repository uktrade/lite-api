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


class QueueViewSerializer(serializers.ModelSerializer):
    is_system_queue = serializers.SerializerMethodField()

    def get_is_system_queue(self, instance):
        return instance.id in SYSTEM_QUEUES

    class Meta:
        model = Queue
        fields = ("id", "name", "is_system_queue")


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

    class Meta:
        model = Queue
        fields = (
            "id",
            "name",
            "team",
        )
