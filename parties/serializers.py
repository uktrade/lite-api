from rest_framework import serializers, relations

from conf.serializers import KeyValueChoiceField, CountrySerializerField
from organisations.models import Organisation
from parties.document.models import PartyDocument
from parties.enums import PartyType, SubType, ThirdPartySubType
from parties.models import Party, EndUser, UltimateEndUser, Consignee, ThirdParty


class PartySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = CountrySerializerField()
    website = serializers.URLField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=PartyType.choices, required=False)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    document = serializers.SerializerMethodField()

    class Meta:
        model = Party
        fields = (
            "id",
            "name",
            "address",
            "country",
            "website",
            "type",
            "organisation",
            "document",
        )

    def get_document(self, instance):
        docs = PartyDocument.objects.filter(party=instance).values()
        return docs[0] if docs else None


class EndUserSerializer(PartySerializer):
    sub_type = KeyValueChoiceField(choices=SubType.choices)

    class Meta:
        model = EndUser

        fields = "__all__"


class UltimateEndUserSerializer(PartySerializer):
    sub_type = KeyValueChoiceField(choices=SubType.choices)

    class Meta:
        model = UltimateEndUser

        fields = "__all__"


class ConsigneeSerializer(PartySerializer):
    sub_type = KeyValueChoiceField(choices=SubType.choices)

    class Meta:
        model = Consignee

        fields = "__all__"


class ThirdPartySerializer(PartySerializer):
    sub_type = KeyValueChoiceField(choices=ThirdPartySubType.choices)

    class Meta:
        model = ThirdParty

        fields = "__all__"
