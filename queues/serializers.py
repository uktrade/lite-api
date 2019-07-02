from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from cases.models import Case, CaseAssignment
from cases.serializers import CaseSerializer
from gov_users.models import GovUser
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


class CaseAssignmentSerializer(serializers.ModelSerializer):
    case = PrimaryKeyRelatedField(many=False, queryset=Case.objects.all())
    user = PrimaryKeyRelatedField(many=False, queryset=GovUser.objects.all())
    queue = PrimaryKeyRelatedField(many=False, queryset=Queue.objects.all())

    class Meta:
        model = CaseAssignment
        fields = ('id', 'case', 'queue', 'user')
