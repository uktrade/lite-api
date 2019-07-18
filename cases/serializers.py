from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.serializers import ApplicationBaseSerializer
from case_types.serializers import CaseTypeSerializer
from cases.models import Case, CaseNote, CaseAssignment
from clc_queries.serializers import ClcQuerySerializer
from content_strings.strings import get_string
from gov_users.serializers import GovUserSimpleSerializer
from queues.models import Queue
from users.models import BaseUser
from users.serializers import BaseUserViewSerializer


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
        if not attrs:
            raise serializers.ValidationError(get_string('cases.assign_queues.select_at_least_one_queue'))
        return attrs


class CaseNoteViewSerializer(serializers.ModelSerializer):
    """
    Serializes case notes
    """
    user = BaseUserViewSerializer()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CaseNote
        fields = '__all__'


class CaseNoteCreateSerializer(CaseNoteViewSerializer):
    """
    Serializes case notes
    """
    text = serializers.CharField(min_length=2, max_length=2200)
    case = PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedField(queryset=BaseUser.objects.all())
    created_at = serializers.DateTimeField(read_only=True)
    is_visible_to_exporter = serializers.BooleanField(default=False)

    class Meta:
        model = CaseNote
        fields = '__all__'


class CaseAssignmentSerializer(serializers.ModelSerializer):
    users = GovUserSimpleSerializer(many=True)

    class Meta:
        model = CaseAssignment
        fields = ('case', 'users')
