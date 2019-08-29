from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from cases.models import Case, CaseNote
from clc_queries.models import ClcQuery
from conf.settings import BACKGROUND_TASK_ENABLED
from documents.tasks import prepare_document
from flags.enums import FlagStatuses
from goods.enums import GoodStatus, GoodControlled
from goods.models import Good, GoodDocument
from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer
from users.models import ExporterUser
from users.serializers import ExporterUserSimpleSerializer


class GoodSerializer(serializers.ModelSerializer):

    description = serializers.CharField(max_length=280)
    is_good_controlled = serializers.ChoiceField(choices=GoodControlled.choices)
    control_code = serializers.CharField(required=False, default="", allow_blank=True)
    is_good_end_product = serializers.BooleanField()
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = serializers.ChoiceField(choices=GoodStatus.choices)
    not_sure_details_details = serializers.CharField(allow_blank=True, required=False)
    clc_query_case_id = serializers.SerializerMethodField()
    clc_query_id = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = Good
        fields = ('id',
                  'description',
                  'is_good_controlled',
                  'clc_query_case_id',
                  'control_code',
                  'is_good_end_product',
                  'part_number',
                  'organisation',
                  'status',
                  'not_sure_details_details',
                  'notes',
                  'clc_query_id',
                  'documents',
                  )

    def __init__(self, *args, **kwargs):
        super(GoodSerializer, self).__init__(*args, **kwargs)

        # Only validate the control code if the good is controlled
        if self.get_initial().get('is_good_controlled') == GoodControlled.YES:
            self.fields['control_code'] = serializers.CharField(required=True)

    # pylint: disable=W0703
    def get_clc_query_case_id(self, instance):
        try:
            clc_query = ClcQuery.objects.filter(good=instance)[0]
            case = Case.objects.filter(clc_query=clc_query)[0]
            return case.id
        except Exception:
            return None

    def get_clc_query_id(self, instance):
        try:
            clc_query = ClcQuery.objects.filter(good=instance)[0]
            return clc_query.id
        except Exception:
            return None

    def get_notes(self, instance):
        from cases.serializers import CaseNoteSerializer  # circular import prevention
        try:
            clc_query = ClcQuery.objects.get(good=instance)
            case = Case.objects.get(clc_query=clc_query)
            case_notes = CaseNote.objects.filter(case=case)

            return CaseNoteSerializer(case_notes, many=True).data
        except Exception:
            return None

    def get_documents(self, instance):
        documents = GoodDocument.objects.filter(good=instance)
        if documents:
            return SimpleGoodDocumentViewSerializer(documents, many=True).data
        return None

    # pylint: disable=W0221
    def validate(self, value):
        is_controlled_good = value.get('is_good_controlled') == GoodControlled.YES
        if is_controlled_good and not value.get('control_code'):
            raise serializers.ValidationError('Control Code must be set when good is controlled')

        return value

    def create(self, validated_data):
        good = super(GoodSerializer, self).create(validated_data)
        return good

    def update(self, instance, validated_data):
        instance.description = validated_data.get('description', instance.description)
        instance.is_good_controlled = validated_data.get('is_good_controlled', instance.is_good_controlled)
        instance.control_code = validated_data.get('control_code', instance.control_code)
        instance.is_good_end_product = validated_data.get('is_good_end_product', instance.is_good_end_product)
        instance.part_number = validated_data.get('part_number', instance.part_number)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance


class GoodDocumentCreateSerializer(serializers.ModelSerializer):
    good = serializers.PrimaryKeyRelatedField(queryset=Good.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all())
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = GoodDocument
        fields = ('name', 's3_key', 'user', 'organisation', 'size', 'good', 'description')

    def create(self, validated_data):
        good_document = super(GoodDocumentCreateSerializer, self).create(validated_data)
        good_document.save()

        if BACKGROUND_TASK_ENABLED:
            prepare_document(str(good_document.id))
        else:
            # pylint: disable=W0703
            try:
                prepare_document.now(str(good_document.id))
            except Exception:
                raise serializers.ValidationError({'errors': {'document': 'Failed to upload'}})

        return good_document


class GoodDocumentViewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    good = serializers.PrimaryKeyRelatedField(queryset=Good.objects.all())
    user = ExporterUserSimpleSerializer()
    organisation = OrganisationViewSerializer()
    s3_key = serializers.SerializerMethodField()

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else 'File not ready'

    class Meta:
        model = GoodDocument
        fields = ('id', 'name', 's3_key', 'user', 'organisation', 'size', 'good', 'created_at', 'safe', 'description')


class SimpleGoodDocumentViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoodDocument
        fields = ('id', 'name', 'description', 'size', 'safe')


class FullGoodSerializer(GoodSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values('id', 'name'))

    class Meta:
        model = Good
        fields = '__all__'
