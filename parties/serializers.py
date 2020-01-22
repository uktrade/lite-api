from django.core.validators import URLValidator
from rest_framework import serializers, relations

from conf.serializers import KeyValueChoiceField, CountrySerializerField
from documents.libraries.process_document import process_document
from lite_content.lite_api.strings import Parties
from organisations.models import Organisation
from parties.models import PartyDocument
from parties.enums import PartyType, SubType, ThirdPartyRole
from parties.models import Party, UltimateEndUser, ThirdParty


class PartySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = CountrySerializerField()
    website = serializers.CharField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=PartyType.choices, required=False)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    document = serializers.SerializerMethodField()
    sub_type = KeyValueChoiceField(choices=SubType.choices, error_messages={"required": Parties.NULL_TYPE})

    class Meta:
        model = Party
        fields = ("id", "name", "address", "country", "website", "type", "organisation", "document", "sub_type")

    @staticmethod
    def validate_website(value):
        """
        Custom validation for URL that makes use of django URLValidator
        but makes the passing of http:// or https:// optional by prepending
        it if not given. Raises a validation error passed back to the user if
        invalid. Does not validate if value is empty
        :param value: given value for URL
        :return: string to save for the website field
        """
        if value:
            validator = URLValidator()
            if "https://" not in value and "http://" not in value:
                # Prepend string with https:// so user doesn't have to
                value = f"https://{value}"
            validator(value)
            return value
        else:
            # Field is optional so doesn't validate if blank and just saves an empty string
            return ""

    def get_document(self, instance):
        docs = PartyDocument.objects.filter(party=instance).values()
        return docs[0] if docs else None


class EndUserSerializer(PartySerializer):
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
            "sub_type",
        )


class EndUserWithFlagsSerializer(EndUserSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.values("id", "name"))

    class Meta:
        model = Party
        fields = "__all__"


class UltimateEndUserSerializer(PartySerializer):
    class Meta:
        model = UltimateEndUser
        fields = (
            "id",
            "name",
            "address",
            "country",
            "website",
            "type",
            "organisation",
            "document",
            "sub_type",
        )


class UltimateEndUserWithFlagsSerializer(UltimateEndUserSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.values("id", "name"))

    class Meta:
        model = UltimateEndUser
        fields = "__all__"


class ConsigneeSerializer(PartySerializer):
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
            "sub_type",
        )


class ConsigneeWithFlagsSerializer(ConsigneeSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.values("id", "name"))

    class Meta:
        model = Party
        fields = "__all__"


class ThirdPartySerializer(PartySerializer):
    role = KeyValueChoiceField(
        choices=ThirdPartyRole.choices, error_messages={"required": Parties.ThirdParty.NULL_ROLE}
    )

    class Meta:
        model = ThirdParty
        fields = ("id", "name", "address", "country", "website", "type", "organisation", "document", "sub_type", "role")


class ThirdPartyWithFlagsSerializer(ThirdPartySerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.values("id", "name"))

    class Meta:
        model = ThirdParty
        fields = "__all__"


class PartyDocumentSerializer(serializers.ModelSerializer):
    party = serializers.PrimaryKeyRelatedField(queryset=Party.objects.all())

    class Meta:
        model = PartyDocument
        fields = (
            "id",
            "name",
            "s3_key",
            "size",
            "party",
            "safe",
        )

    def create(self, validated_data):
        document = super(PartyDocumentSerializer, self).create(validated_data)
        document.save()
        process_document(document)
        return document


class PartyWithFlagsSerializer(PartySerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.values("id", "name"))

    class Meta:
        model = Party
        fields = "__all__"
