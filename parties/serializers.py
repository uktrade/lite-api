from rest_framework import serializers, relations

from documents.libraries.process_document import process_document
from parties.document.models import EndUserDocument
from parties.enums import PartyType
from parties.models import Party
from organisations.models import Organisation
from static.countries.models import Country


class PartySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    website = serializers.URLField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=PartyType.choices)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
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
                  'document')

    def get_document(self, instance):
        docs = EndUserDocument.objects.filter(end_user=instance).values()
        return docs[0] if docs else None


class PartyDocumentSerializer(serializers.ModelSerializer):
    party = serializers.PrimaryKeyRelatedField(queryset=Party.objects.all())

    class Meta:
        model = EndUserDocument
        fields = ('id', 'name', 's3_key', 'size', 'parties', 'safe')

    def create(self, validated_data):
        party_document = super(PartyDocumentSerializer, self).create(validated_data)
        party_document.save()
        process_document(party_document)
        return party_document
