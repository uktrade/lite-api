from django.core.validators import URLValidator
from rest_framework import serializers, relations

from conf.serializers import KeyValueChoiceField, CountrySerializerField
from documents.libraries.process_document import process_document
from lite_content.lite_api.strings import Parties
from organisations.models import Organisation
from parties.enums import PartyType, SubType, PartyRole
from parties.models import Party
from parties.models import PartyDocument


class FlagSerializer(serializers.Serializer):
    name = serializers.CharField()
    id = serializers.CharField()

class CountrySerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    name = serializers.CharField()
    type = serializers.CharField(required=False)
    is_eu = serializers.CharField(required=False)


class PartySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = CountrySerializerField()
    website = serializers.CharField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=PartyType.choices)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    document = serializers.SerializerMethodField()
    sub_type = KeyValueChoiceField(choices=SubType.choices, error_messages={"required": Parties.NULL_TYPE})
    role = KeyValueChoiceField(
        choices=PartyRole.choices, error_messages={"required": Parties.ThirdParty.NULL_ROLE}, required=False
    )
    flags = FlagSerializer(many=True, required=False)
    copy_of = relations.PrimaryKeyRelatedField(queryset=Party.objects.all(), allow_null=True, required=False)

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
            "role",
            "flags",
            "copy_of",
        )

    def __init__(self, *args, **kwargs):
        super(PartySerializer, self).__init__(*args, **kwargs)
        #
        #
        # print('1-------------')
        # print(args)
        # print(kwargs)
        # print(kwargs.get("data"))
        # Pre-validation: update required parameter on serializer fields at PartyType level
        if "data" in kwargs and "type" in kwargs["data"]:
            party_type = kwargs["data"]["type"]

            if party_type == PartyType.THIRD_PARTY:
                for field, serializer_instance in self.fields.items():
                    if field == "role":
                        serializer_instance.required = True

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
        docs = PartyDocument.objects.filter(party=instance)
        return docs.values()[0] if docs.exists() else None


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
