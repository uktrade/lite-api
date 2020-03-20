from django.core.validators import URLValidator
from rest_framework import serializers, relations

from cases.enums import CaseTypeSubTypeEnum
from conf.serializers import KeyValueChoiceField, CountrySerializerField
from documents.libraries.process_document import process_document
from flags.serializers import FlagSerializer
from goods.enums import PvGrading
from lite_content.lite_api.strings import PartyErrors
from organisations.models import Organisation
from parties.enums import PartyType, SubType, PartyRole
from parties.models import Party
from parties.models import PartyDocument


class PartySerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages=PartyErrors.NAME)
    address = serializers.CharField(error_messages=PartyErrors.ADDRESS)
    country = CountrySerializerField()
    website = serializers.CharField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=PartyType.choices, error_messages=PartyErrors.TYPE)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    document = serializers.SerializerMethodField()
    sub_type = KeyValueChoiceField(choices=SubType.choices, error_messages=PartyErrors.SUB_TYPE)
    role = KeyValueChoiceField(choices=PartyRole.choices, error_messages=PartyErrors.ROLE, required=False)
    flags = FlagSerializer(many=True, required=False)
    clearance_level = KeyValueChoiceField(choices=PvGrading.choices, allow_null=True, required=False, allow_blank=True)
    descriptors = serializers.CharField(allow_null=True, required=False, allow_blank=True)
    copy_of = relations.PrimaryKeyRelatedField(queryset=Party.objects.all(), allow_null=True, required=False)
    deleted_at = serializers.DateTimeField(allow_null=True, required=False)

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
            "deleted_at",
            "clearance_level",
            "descriptors",
        )

    def __init__(self, *args, **kwargs):
        application_type = kwargs.pop("application_type", None)

        super(PartySerializer, self).__init__(*args, **kwargs)
        party_type = kwargs.get("data", {}).get("type")
        if party_type == PartyType.THIRD_PARTY:
            for field, serializer_instance in self.fields.items():
                if field == "role":
                    serializer_instance.required = True
                if self.initial_data.get("sub_type") == "other":
                    if field == "descriptors" and application_type != CaseTypeSubTypeEnum.F680:
                        serializer_instance.required = True
                        serializer_instance.allow_blank = False

        if application_type == CaseTypeSubTypeEnum.F680:
            for field, serializer_instance in self.fields.items():
                if field == "clearance_level":
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


class AdditionalContactSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages=PartyErrors.NAME)
    email = serializers.EmailField(error_messages=PartyErrors.EMAIL)
    phone_number = serializers.CharField(error_messages=PartyErrors.PHONE_NUMBER)
    details = serializers.CharField(error_messages=PartyErrors.DETAILS)
    address = serializers.CharField(error_messages=PartyErrors.ADDRESS)
    country = CountrySerializerField()
    type = KeyValueChoiceField(choices=PartyType.choices, required=True)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = Party
        fields = (
            "id",
            "name",
            "phone_number",
            "email",
            "details",
            "address",
            "country",
            "type",
            "organisation",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, "initial_data"):
            self.initial_data["type"] = PartyType.ADDITIONAL_CONTACT
            self.initial_data["organisation"] = self.context["organisation_pk"]
