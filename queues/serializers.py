import uuid

from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from cases.serializers import CaseSerializer
from queues.models import Queue
from teams.models import Team


class QueueSerializer(serializers.ModelSerializer):
    cases = CaseSerializer(many=True, read_only=True, required=False)
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())
    team_name = serializers.SerializerMethodField()

    class Meta:
        model = Queue
        fields = ('id',
                  'name',
                  'team',
                  'team_name',
                  'cases')

    def get_team_name(self, obj):
        return obj.team.name

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
