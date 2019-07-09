from rest_framework import serializers

from applications.serializers import ApplicationBaseSerializer
from cases.models import Case, CaseNote, CaseAssignment, CaseDocument
from conf.settings import ASYNC_DOC_PREPARE
from content_strings.strings import get_string
# from documents.serializers import DocumentSerializer
from gov_users.models import GovUser
from gov_users.serializers import GovUserSimpleSerializer
from queues.models import Queue
from documents.tasks import prepare_document


class CaseSerializer(serializers.ModelSerializer):
    """
    Serializes cases
    """
    application = ApplicationBaseSerializer(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'application')


class CaseDetailSerializer(CaseSerializer):
    queues = serializers.PrimaryKeyRelatedField(many=True, queryset=Queue.objects.all())

    class Meta:
        model = Case
        fields = ('id', 'application', 'queues')

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
    # size = serializers.IntegerField(max_value=500,
    #                                 error_messages={
    #                                     'max_value': get_string('documents.max_value')
    #                                 })  # Max file size is 500mb
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=GovUser.objects.all())

    class Meta:
        model = CaseDocument
        fields = ('name', 's3_key', 'user', 'size', 'case', 'description')

    def create(self, validated_data):
        case_document = super(CaseDocumentCreateSerializer, self).create(validated_data)
        case_document.save()
        # if ASYNC_DOC_PREPARE:
        prepare_document(case_document.id)
        # elif not ASYNC_DOC_PREPARE and document.safe is None:
        #     prepare_document.run(document.id, case.id if case else None)
        return case_document


class CaseDocumentViewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = GovUserSimpleSerializer()

    class Meta:
        model = CaseDocument
        fields = ('name', 's3_key', 'user', 'size', 'case', 'created_at', 'description')
