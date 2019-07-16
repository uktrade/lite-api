from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.serializers import ApplicationBaseSerializer
from cases.models import Case, CaseNote, CaseAssignment, CaseFlags
from content_strings.strings import get_string
from clc_queries.serializers import ClcQuerySerializer
from gov_users.models import GovUser
from gov_users.serializers import GovUserSimpleSerializer
from case_types.serializers import CaseTypeSerializer
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
    is_clc = serializers.SerializerMethodField()
    clc_query = ClcQuerySerializer(read_only=True)
    case_type = CaseTypeSerializer(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'application', 'queues', 'is_clc', 'clc_query', 'case_type')

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


class CaseFlagSerializer(serializers.ModelSerializer):
    """
    Serializes flags on case
    """
    case = PrimaryKeyRelatedField(queryset=Case.objects.all())
    flag = PrimaryKeyRelatedField(queryset=Flag.objects.all())
    flag_name = serializers.SerializerMethodField()

    class Meta:
        model = CaseFlags
        fields = ('id', 'case', 'flag', 'flag_name')

    def __init__(self, *args, **kwargs):
        super(CaseFlagSerializer, self).__init__(*args, **kwargs)

        # Don't return id or case_id if the request is a GET
        # Don't validate flag_name if the request is a POST
        if self.context['method'] == "GET":
            del self.fields['id']
            del self.fields['case']

    # pylint: disable=W0703
    def get_flag_name(self, instance):
        try:
            return instance.flag.name
        except Exception:
            return None

    def validate_flag(self, value):
        if value not in self.context['team_case_level_flags']:
            raise serializers.ValidationError('You can only assign flags that are available for your team.')
        return value
