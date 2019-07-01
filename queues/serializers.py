from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from cases.models import Case, CaseAssignment
from cases.serializers import CaseSerializer
from gov_users.models import GovUser
from queues.models import Queue

from teams.models import Team
from teams.serializers import TeamSerializer


class QueueSerializer(serializers.ModelSerializer):
    cases = CaseSerializer(many=True, read_only=True, required=False)
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())

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


class QueueViewSerializer(QueueSerializer):
    team = TeamSerializer(required=False)

    class Meta:
        model = Queue
        fields = ('id',
                  'name',
                  'team',
                  'cases',)


class CaseAssignmentSerializer(serializers.ModelSerializer):
    cases = PrimaryKeyRelatedField(many=True, queryset=Case.objects.all())
    users = PrimaryKeyRelatedField(many=True, queryset=GovUser.objects.all())
    queue = PrimaryKeyRelatedField(many=False, queryset=Queue.objects.all())

    class Meta:
        model = CaseAssignment
        fields = ('id', 'cases', 'queue', 'users')
