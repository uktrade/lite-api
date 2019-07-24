from rest_framework import serializers

from applications.serializers import ApplicationBaseSerializer
from case_types.serializers import CaseTypeSerializer
from cases.models import Case, CaseNote, CaseAssignment, CaseDocument
from clc_queries.serializers import ClcQuerySerializer
from conf.settings import BACKGROUND_TASK_ENABLED
from content_strings.strings import get_string
from gov_users.serializers import GovUserSimpleSerializer
from queues.models import Queue
from users.models import BaseUser, GovUser
from users.serializers import BaseUserViewSerializer
from flags.models import Flag
from documents.tasks import prepare_document


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
    queues = serializers.PrimaryKeyRelatedField(many=True, queryset=Queue.objects.all())
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
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=BaseUser.objects.all())
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


class CaseFlagsAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializes flags on case
    """
    flags = serializers.PrimaryKeyRelatedField(queryset=Flag.objects.all(), many=True)

    class Meta:
        model = Case
        fields = ('id', 'flags')

    def validate_flags(self, flags):
        team_case_level_flags = list(Flag.objects.filter(level='Case', team=self.context['team']))
        if not set(flags).issubset(list(team_case_level_flags)):
            raise serializers.ValidationError('You can only assign case-level flags that are available to your team.')
        return flags


class CaseDocumentCreateSerializer(serializers.ModelSerializer):
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=GovUser.objects.all())

    class Meta:
        model = CaseDocument
        fields = ('name', 's3_key', 'user', 'size', 'case', 'description')

    def create(self, validated_data):
        case_document = super(CaseDocumentCreateSerializer, self).create(validated_data)
        case_document.save()

        if BACKGROUND_TASK_ENABLED:
            prepare_document(str(case_document.id))
        else:
            try:
                prepare_document.now(str(case_document.id))
            except Exception:
                raise serializers.ValidationError({'errors': {'document': 'Failed to upload'}})

        return case_document


class CaseDocumentViewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = GovUserSimpleSerializer()
    s3_key = serializers.SerializerMethodField()

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else 'File not ready'

    class Meta:
        model = CaseDocument
        fields = ('name', 's3_key', 'user', 'size', 'case', 'created_at', 'safe', 'description')
