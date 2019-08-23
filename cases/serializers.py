from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from applications.serializers import ApplicationBaseSerializer
from cases.enums import CaseType, AdviceType
from cases.models import Case, CaseNote, CaseAssignment, CaseDocument, Advice, EcjuQuery
from clc_queries.serializers import ClcQuerySerializer
from conf.helpers import convert_queryset_to_str, ensure_x_items_not_none
from conf.serializers import KeyValueChoiceField, PrimaryKeyRelatedSerializerField
from conf.settings import BACKGROUND_TASK_ENABLED
from content_strings.strings import get_string
from documents.tasks import prepare_document
from end_user.models import EndUser
from flags.models import Flag
from goods.models import Good
from goodstype.models import GoodsType
from gov_users.serializers import GovUserSimpleSerializer
from queues.models import Queue
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from users.models import BaseUser, GovUser
from users.serializers import BaseUserViewSerializer, GovUserViewSerializer


class CaseSerializer(serializers.ModelSerializer):
    """
    Serializes cases
    """
    type = KeyValueChoiceField(choices=CaseType.choices)
    clc_query = ClcQuerySerializer(read_only=True)
    application = ApplicationBaseSerializer(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'type', 'application', 'clc_query',)

    # pylint: disable=W0221
    def to_representation(self, value):
        """
        Only show 'application' if it has an application inside,
        and only show 'clc_query' if it has a CLC query inside
        """
        repr_dict = super(CaseSerializer, self).to_representation(value)
        if not repr_dict['application']:
            del repr_dict['application']
        if not repr_dict['clc_query']:
            del repr_dict['clc_query']
        return repr_dict


class CaseDetailSerializer(CaseSerializer):
    queues = serializers.PrimaryKeyRelatedField(many=True, queryset=Queue.objects.all())
    queue_names = serializers.SerializerMethodField()
    flags = serializers.SerializerMethodField()
    clc_query = ClcQuerySerializer(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'type', 'flags', 'queues', 'queue_names', 'application', 'clc_query',)

    def get_flags(self, instance):
        return list(instance.flags.all().values('id', 'name'))

    def get_queue_names(self, instance):
        return list(instance.queues.values_list('name', flat=True))

    def validate_queues(self, attrs):
        if not attrs:
            raise serializers.ValidationError(get_string('cases.assign_queues.select_at_least_one_queue'))
        return attrs


class CaseNoteSerializer(serializers.ModelSerializer):
    """
    Serializes case notes
    """
    text = serializers.CharField(min_length=2, max_length=2200)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedSerializerField(queryset=BaseUser.objects.all(), serializer=BaseUserViewSerializer)
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


class CaseAdviceSerializer(serializers.ModelSerializer):
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedSerializerField(queryset=GovUser.objects.all(),
                                            serializer=GovUserViewSerializer)
    proviso = serializers.CharField(required=False,
                                    allow_blank=False,
                                    allow_null=False,
                                    error_messages={'blank': 'Enter a proviso'},
                                    max_length=5000)
    text = serializers.CharField(required=True,
                                 allow_blank=False,
                                 allow_null=False,
                                 error_messages={'blank': 'Enter some advice'},
                                 max_length=5000)
    note = serializers.CharField(required=False,
                                 allow_blank=True,
                                 allow_null=True,
                                 max_length=200)
    type = KeyValueChoiceField(choices=AdviceType.choices)
    denial_reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(),
                                                        many=True,
                                                        required=False)

    # Optional fields
    good = serializers.PrimaryKeyRelatedField(queryset=Good.objects.all(), required=False)
    goods_type = serializers.PrimaryKeyRelatedField(queryset=GoodsType.objects.all(), required=False)
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), required=False)
    end_user = serializers.PrimaryKeyRelatedField(queryset=EndUser.objects.all(), required=False)
    ultimate_end_user = serializers.PrimaryKeyRelatedField(queryset=EndUser.objects.all(), required=False)

    class Meta:
        model = Advice
        fields = ('case', 'user', 'text', 'note', 'type', 'proviso', 'denial_reasons',
                  'good', 'goods_type', 'country', 'end_user', 'ultimate_end_user', 'created_at')

    def validate_denial_reasons(self, value):
        """
        Check that the denial reasons are set if type is REFUSE
        """
        for data in self.initial_data:
            if data['type'] == AdviceType.REFUSE and not data['denial_reasons']:
                raise serializers.ValidationError('Select at least one denial reason')

        return value

    def validate_proviso(self, value):
        """
        Check that the proviso is set if type is REFUSE
        """
        for data in self.initial_data:
            if data['type'] == AdviceType.PROVISO and not data['proviso']:
                raise ValidationError('Provide a proviso')

        return value

    def __init__(self, *args, **kwargs):
        super(CaseAdviceSerializer, self).__init__(*args, **kwargs)

        application_fields = ['good',
                              'goods_type',
                              'country',
                              'end_user',
                              'ultimate_end_user']

        # Ensure only one item is provided
        if hasattr(self, 'initial_data'):
            for data in self.initial_data:
                if not ensure_x_items_not_none([data.get(x) for x in application_fields], 1):
                    raise ValidationError('Only one item (such as an end_user) can be given at a time')

    def to_representation(self, instance):
        repr_dict = super(CaseAdviceSerializer, self).to_representation(instance)

        if instance.type == AdviceType.PROVISO:
            repr_dict['proviso'] = instance.proviso
        else:
            del repr_dict['proviso']

        if instance.type == AdviceType.REFUSE:
            repr_dict['denial_reasons'] = convert_queryset_to_str(instance.denial_reasons.values_list('id', flat=True))
        else:
            del repr_dict['denial_reasons']

        return repr_dict


class EcjuQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = EcjuQuery
        fields = ('id',
                  'question',
                  'response',
                  'case',)


class EcjuQueryCreateSerializer(serializers.ModelSerializer):
    """
    Create specific serializer, which does not take a response as gov users don't respond to their own queries!
    """
    question = serializers.CharField(max_length=5000, allow_blank=False, allow_null=False)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())

    class Meta:
        model = EcjuQuery
        fields = ('id',
                  'question',
                  'case',
                  'raised_by_user',)
