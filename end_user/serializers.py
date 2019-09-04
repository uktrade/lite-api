from rest_framework import serializers, relations

from conf.serializers import KeyValueChoiceField, PrimaryKeyRelatedSerializerField
from documents.libraries.process_document import process_document
from end_user.document.models import EndUserDocument
from end_user.enums import EndUserType
from end_user.models import EndUser
from organisations.models import Organisation
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class EndUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, max_length=50)
    address = serializers.CharField(required=True)
    country = PrimaryKeyRelatedSerializerField(queryset=Country.objects.all(), required=True, serializer=CountrySerializer)
    website = serializers.URLField(required=False, allow_blank=True)
    type = KeyValueChoiceField(choices=EndUserType.choices, required=True, allow_blank=False, allow_null=False)
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
        fields = ('id', 'name', 's3_key', 'size', 'end_user', 'safe')

    def create(self, validated_data):
        end_user_document = super(EndUserDocumentSerializer, self).create(validated_data)
        end_user_document.save()
        process_document(end_user_document)
        return end_user_document
