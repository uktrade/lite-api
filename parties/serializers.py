from rest_framework import serializers, relations

from applications.models import Application
from documents.libraries.process_document import process_document
from drafts.models import Draft
from parties.document.models import EndUserDocument
from parties.enums import PartyType
from parties.models import Party, EndUser, UltimateEndUser, Consignee
from organisations.models import Organisation
from static.countries.models import Country


class PartySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    website = serializers.URLField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=PartyType.choices)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    application = relations.PrimaryKeyRelatedField(queryset=Application.objects.all())
    draft = relations.PrimaryKeyRelatedField(queryset=Draft.objects.all())
    document = serializers.SerializerMethodField()

    class Meta:
        model = Party
        fields = ('id',
                  'name',
                  'address',
                  'country',
                  'website',
                  'type',
                  'organisation',
                  'document',
                  'application',
                  'draft')

    def get_document(self, instance):
        docs = EndUserDocument.objects.filter(end_user=instance).values()
        return docs[0] if docs else None


class EndUserSerializer(PartySerializer):
    class Meta:
        model = EndUser

        fields = '__all__'


class UltimateEndUserSerializer(PartySerializer):
    class Meta:
        model = UltimateEndUser

        fields = '__all__'


class ConsigneeSerializer(PartySerializer):
    class Meta:
        model = Consignee

        fields = '__all__'


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
