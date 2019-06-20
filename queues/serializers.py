from rest_framework import serializers

from cases.serializers import CaseSerializer
from queues.models import Queue
from teams.serializers import TeamSerializer


class QueueSerializer(serializers.ModelSerializer):
    cases = CaseSerializer(many=True, read_only=True, required=False)
    team = TeamSerializer(required=False)

    class Meta:
        model = Queue
        fields = ('id',
                  'name',
                  'team',
                  'cases',)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
