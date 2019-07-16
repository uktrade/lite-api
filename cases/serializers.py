from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.serializers import ApplicationBaseSerializer
from case_types.serializers import CaseTypeSerializer
from cases.models import Case, CaseNote, CaseAssignment, CaseDocument
from clc_queries.serializers import ClcQuerySerializer
from conf.settings import BACKGROUND_TASK_ENABLED
from content_strings.strings import get_string
from gov_users.models import GovUser
from gov_users.serializers import GovUserSimpleSerializer
from queues.models import Queue
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
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=GovUser.objects.all())
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CaseNote
        fields = ('id', 'text', 'case', 'user', 'created_at')


class CaseAssignmentSerializer(serializers.ModelSerializer):
    users = GovUserSimpleSerializer(many=True)

    class Meta:
        model = CaseAssignment
        fields = ('case', 'users')


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
            prepare_document.now(str(case_document.id))
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
