from rest_framework import serializers, relations

from conf.settings import BACKGROUND_TASK_ENABLED
from documents.tasks import prepare_document
from end_user.end_user_document.models import EndUserDocument, DraftEndUserDocument
from end_user.enums import EndUserType
from end_user.models import EndUser
from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer
from static.countries.models import Country
from users.models import ExporterUser
from users.serializers import ExporterUserSimpleSerializer


class EndUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    website = serializers.URLField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=EndUserType.choices)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = EndUser
        fields = ('id',
                  'name',
                  'address',
                  'country',
                  'website',
                  'type',
                  'organisation')

    def update(self, instance, validated_data):
        """
        Update and return an existing `Site` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.address = validated_data.get('address', instance.address)
        instance.country = validated_data.get('country', instance.country)
        instance.website = validated_data.get('website', instance.website)
        instance.type = validated_data.get('type', instance.type)
        instance.save()
        return instance


class EndUserDocumentViewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    end_user = serializers.PrimaryKeyRelatedField(queryset=EndUser.objects.all())
    user = ExporterUserSimpleSerializer()
    organisation = OrganisationViewSerializer()
    s3_key = serializers.SerializerMethodField()

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else 'File not ready'

    class Meta:
        model = EndUserDocument
        fields = ('id', 'name', 's3_key', 'user', 'organisation', 'size', 'good', 'created_at', 'safe', 'description')


class DraftEndUserDocumentSerializer(serializers.ModelSerializer):
    end_user = serializers.PrimaryKeyRelatedField(queryset=EndUser.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all())
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = DraftEndUserDocument
        fields = ('name', 's3_key', 'user', 'organisation', 'size', 'end_user', 'description')

    def create(self, validated_data):
        end_user_document = super(DraftEndUserDocumentSerializer, self).create(validated_data)
        end_user_document.save()

        if BACKGROUND_TASK_ENABLED:
            prepare_document(str(end_user_document.id))
        else:
            try:
                prepare_document.now(str(end_user_document.id))
            except Exception:
                raise serializers.ValidationError({'errors': {'document': 'Failed to upload'}})

        return end_user_document

