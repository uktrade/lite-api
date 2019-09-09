from rest_framework import serializers, relations

from applications.models import Application
from documents.libraries.process_document import process_document
from drafts.models import Draft
from parties.document.models import EndUserDocument
from parties.enums import PartyType, SubType
from parties.models import Party, EndUser, UltimateEndUser, Consignee
from organisations.models import Organisation
from static.countries.models import Country


class PartySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    website = serializers.URLField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=PartyType.choices, required=False)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    application = relations.PrimaryKeyRelatedField(queryset=Application.objects.all(), required=False)
    draft = relations.PrimaryKeyRelatedField(queryset=Draft.objects.all(), required=False)
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

        docs = None
        if instance.type == PartyType.END:
            docs = EndUserDocument.objects.filter(end_user=instance).values()

        return docs[0] if docs else None


class EndUserSerializer(PartySerializer):
    sub_type = serializers.ChoiceField(choices=SubType.choices)

    class Meta:
        model = EndUser

        fields = '__all__'

    def create(self, validated_data):
        end_user = super(EndUserSerializer, self).create(validated_data)
        end_user.type = PartyType.END
        end_user.save()
        return end_user


class UltimateEndUserSerializer(PartySerializer):
    sub_type = serializers.ChoiceField(choices=SubType.choices)

    class Meta:
        model = UltimateEndUser

        fields = '__all__'
        
    def create(self, validated_data):
        ultimate_end_user = super(UltimateEndUserSerializer, self).create(validated_data)
        ultimate_end_user.type = PartyType.ULTIMATE
        ultimate_end_user.save()
        return ultimate_end_user


class ConsigneeSerializer(PartySerializer):
    sub_type = serializers.ChoiceField(choices=SubType.choices)

    class Meta:
        model = Consignee

        fields = '__all__'

    def create(self, validated_data):
        consignee = super(ConsigneeSerializer, self).create(validated_data)
        consignee.type = PartyType.CONSIGNEE
        consignee.save()
        return consignee


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
