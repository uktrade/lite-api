from rest_framework import serializers

from cases.serializers import CaseSerializer
from queues.models import Queue
from teams.serializers import TeamSerializer


class QueueSerializer(serializers.ModelSerializer):
    cases = CaseSerializer(many=True, read_only=True)
    team = TeamSerializer(read_only=True)

    class Meta:
        model = Queue
        fields = ('id',
                  'name',
                  'team',
                  'cases')
