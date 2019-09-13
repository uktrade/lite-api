from rest_framework import serializers, relations
from parties.document.models import PartyDocument
from parties.enums import PartyType, SubType, ThirdPartySubType
from parties.models import Party, EndUser, UltimateEndUser, Consignee, ThirdParty
from organisations.models import Organisation
from static.countries.models import Country


class PartySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    website = serializers.URLField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=PartyType.choices, required=False)
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
                  'document',)

    def get_document(self, instance):
        docs = PartyDocument.objects.filter(party=instance).values()
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


class ThirdPartySerializer(PartySerializer):
    sub_type = serializers.ChoiceField(choices=ThirdPartySubType.choices)

    class Meta:
        model = ThirdParty

        fields = '__all__'

    def create(self, validated_data):
        third_party = super(ThirdPartySerializer, self).create(validated_data)
        third_party.type = PartyType.THIRD
        third_party.save()
        return third_party
