import lite_content.lite_api.queues

from rest_framework import serializers

from cases.models import Case
from cases.serializers import CaseSerializer
from queues.models import Queue
from teams.models import Team
from teams.serializers import TeamSerializer


class QueueViewSerializer(serializers.ModelSerializer):
    team = TeamSerializer(required=False)
    cases_count = serializers.SerializerMethodField()
    is_system_queue = serializers.SerializerMethodField()

    def get_is_system_queue(self, instance):
        # System queues have the attribute 'is_system_queue',
        # hence return whether it has the attribute or not
        return hasattr(instance, "is_system_queue")

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


class QueueCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages={"blank": lite_content.lite_api.queues.Queues.BLANK_NAME,})
    cases = CaseSerializer(many=True, read_only=True, required=False)
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())

    class Meta:
        model = Queue
        fields = (
            "id",
            "name",
            "team",
            "cases",
        )
