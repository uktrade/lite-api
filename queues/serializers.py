from rest_framework import serializers

from cases.serializers import CaseSerializer, CaseDetailSerializer
from content_strings.strings import get_string
from queues.models import Queue
from teams.models import Team
from teams.serializers import TeamSerializer


class QueueSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages={
        'blank': get_string('queues.blank_name'),
    })
    cases = CaseSerializer(many=True, read_only=True, required=False)
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())

    class Meta:
        model = Queue
        fields = ('id',
                  'name',
                  'team',
                  'cases',)


class QueueViewSerializer(QueueSerializer):
    team = TeamSerializer(required=False)

    class Meta:
        model = Queue
        fields = ('id',
                  'name',
                  'team',
                  'cases',)


class AllCasesQueueViewSerializer(QueueSerializer):
    team = TeamSerializer(required=False)
    cases = CaseDetailSerializer(many=True)

    class Meta:
        model = Queue
        fields = ('id',
                  'name',
                  'team',
                  'cases',)
