from rest_framework import serializers

from cases.models import Case
from lite_content.lite_api import strings
from queues.constants import SYSTEM_QUEUES
from queues.models import Queue
from teams.models import Team
from teams.serializers import TeamSerializer


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


class QueueListSerializer(serializers.ModelSerializer):
    team = TeamSerializer(required=False)
    cases_count = serializers.SerializerMethodField()
    is_system_queue = serializers.SerializerMethodField()

    def get_is_system_queue(self, instance):
        return instance.id in SYSTEM_QUEUES

    def get_cases_count(self, instance):
        # System queues have a cases count attribute - use that
        # instead of doing a database lookup
        try:
            return Case.objects.filter(instance.query).distinct().count()
        except AttributeError:
            return instance.cases.count()

    class Meta:
        model = Queue
        fields = ("id", "name", "team", "cases_count", "is_system_queue")


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
