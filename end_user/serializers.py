from rest_framework import serializers, relations

from rest_framework import serializers, relations

import documents
from conf.settings import BACKGROUND_TASK_ENABLED
from end_user.end_user_document.models import EndUserDocument
from end_user.enums import EndUserType
from end_user.models import EndUser
from organisations.models import Organisation
from static.countries.models import Country


class EndUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    website = serializers.URLField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=EndUserType.choices)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    document = serializers.SerializerMethodField()

    class Meta:
        model = EndUser
        fields = ('id',
                  'name',
                  'address',
                  'country',
                  'website',
                  'type',
                  'organisation',
                  'document')

    def get_document(self, instance):
        docs = EndUserDocument.objects.filter(end_user=instance).values()
        return docs[0] if docs else None


class EndUserDocumentSerializer(serializers.ModelSerializer):
    end_user = serializers.PrimaryKeyRelatedField(queryset=EndUser.objects.all())

    class Meta:
        model = EndUserDocument
        fields = ('id', 'name', 's3_key', 'size', 'end_user', 'description', 'safe')

    def create(self, validated_data):
        end_user_document = super(EndUserDocumentSerializer, self).create(validated_data)
        end_user_document.save()

        if BACKGROUND_TASK_ENABLED:
            documents.tasks.prepare_document(str(end_user_document.id))
        else:
            try:
                documents.tasks.prepare_document.now(str(end_user_document.id))
            except Exception:
                raise serializers.ValidationError({'errors': {'document': 'Failed to upload'}})

        return end_user_document
