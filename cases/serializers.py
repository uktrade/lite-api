from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.serializers import ApplicationBaseSerializer
from cases.models import Case, CaseNote, CaseAssignment
from case_types.serializers import CaseTypeSerializer
from clc_queries.serializers import ClcQuerySerializer
from content_strings.strings import get_string
from gov_users.models import GovUser
from gov_users.serializers import GovUserSimpleSerializer
from queues.models import Queue
from flags.models import Flag


class CaseSerializer(serializers.ModelSerializer):
    """
    Serializes cases
    """
    application = ApplicationBaseSerializer(read_only=True)
    is_clc = serializers.SerializerMethodField()
    clc_query = ClcQuerySerializer(read_only=True)
    case_type = CaseTypeSerializer(read_only=True)

    def get_is_clc(self, obj):
        return obj.case_type.name == 'CLC query'

    class Meta:
        model = Case
        fields = ('id', 'application', 'is_clc', 'clc_query', 'case_type')


class CaseDetailSerializer(CaseSerializer):
    queues = PrimaryKeyRelatedField(many=True, queryset=Queue.objects.all())
    flags = serializers.SerializerMethodField()
    is_clc = serializers.SerializerMethodField()
    clc_query = ClcQuerySerializer(read_only=True)
    case_type = CaseTypeSerializer(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'application', 'queues', 'is_clc', 'clc_query', 'case_type', 'flags')

    def get_flags(self, instance):
        return list(instance.flags.all().values('id', 'name'))

    def validate_queues(self, attrs):
        if len(attrs) == 0:
            raise serializers.ValidationError(get_string('cases.assign_queues.select_at_least_one_queue'))
        return attrs


class CaseNoteSerializer(serializers.ModelSerializer):
    """
    Serializes case notes
    """
    text = serializers.CharField(min_length=2, max_length=2200)
    case = PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedField(queryset=GovUser.objects.all())
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CaseNote
        fields = ('id', 'text', 'case', 'user', 'created_at')


class CaseAssignmentSerializer(serializers.ModelSerializer):
    users = GovUserSimpleSerializer(many=True)

    class Meta:
        model = CaseAssignment
        fields = ('case', 'users')


class CaseFlagsAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializes flags on case
    """
    flags = PrimaryKeyRelatedField(queryset=Flag.objects.all(), many=True)

    class Meta:
        model = Case
        fields = ('id', 'flags')

    def validate_flags(self, flags):
        team_case_level_flags = list(Flag.objects.filter(level='Case', team=self.context['team']))
        if not set(flags).issubset(list(team_case_level_flags)):
            raise serializers.ValidationError('You can only assign case-level flags that are available to your team.')
        return flags
