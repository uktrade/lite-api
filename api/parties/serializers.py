from django.core.validators import URLValidator
from rest_framework import serializers, relations

from api.cases.enums import CaseTypeSubTypeEnum
from api.core.serializers import KeyValueChoiceField, CountrySerializerField
from api.documents.libraries.process_document import process_document
from api.flags.serializers import FlagSerializer
from api.goods.enums import PvGrading
from lite_content.lite_api.strings import PartyErrors
from api.organisations.models import Organisation
from api.parties.enums import PartyType, SubType, PartyRole
from api.parties.models import Party
from api.parties.models import PartyDocument


class PartySerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages=PartyErrors.NAME)
    address = serializers.CharField(error_messages=PartyErrors.ADDRESS)
    country = CountrySerializerField()
    website = serializers.CharField(required=False, allow_blank=True)
    signatory_name_euu = serializers.CharField(allow_blank=True)
    type = serializers.ChoiceField(choices=PartyType.choices, error_messages=PartyErrors.TYPE)
    type_display_value = serializers.SerializerMethodField()
    end_user_document_available = serializers.BooleanField(allow_null=True, required=False)
    end_user_document_missing_reason = serializers.CharField(required=False, allow_blank=True)
    product_differences_note = serializers.CharField(required=False, allow_blank=True)
    document_in_english = serializers.BooleanField(allow_null=True, required=False)
    document_on_letterhead = serializers.BooleanField(allow_null=True, required=False)
    ec3_missing_reason = serializers.CharField(required=False, allow_blank=True)
    organisation = relations.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    document = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    role = KeyValueChoiceField(choices=PartyRole.choices, error_messages=PartyErrors.ROLE, required=False)
    role_other = serializers.CharField(
        max_length=75, allow_null=True, allow_blank=True, required=False, error_messages=PartyErrors.ROLE_OTHER
    )
    sub_type = KeyValueChoiceField(choices=SubType.choices, error_messages=PartyErrors.SUB_TYPE)
    sub_type_other = serializers.CharField(
        max_length=75, allow_null=True, allow_blank=True, required=False, error_messages=PartyErrors.SUB_TYPE_OTHER
    )
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
            "signatory_name_euu",
            "type",
            "type_display_value",
            "organisation",
            "document",
            "documents",
            "sub_type",
            "sub_type_other",
            "end_user_document_available",
            "end_user_document_missing_reason",
            "product_differences_note",
            "document_in_english",
            "document_on_letterhead",
            "ec3_missing_reason",
            "role",
            "role_other",
            "flags",
            "copy_of",
            "deleted_at",
            "clearance_level",
            "descriptors",
        )

    def __init__(self, *args, **kwargs):
        application_type = kwargs.pop("application_type", None)
        super(PartySerializer, self).__init__(*args, **kwargs)

        if hasattr(self, "initial_data"):
            party_type = kwargs.get("data", {}).get("type")
            role = self.initial_data.get("role")
            sub_type = self.initial_data.get("sub_type")

            if party_type != PartyType.END_USER:
                self.fields["signatory_name_euu"].required = False

            if sub_type == SubType.OTHER:
                self.fields["sub_type_other"].required = True
                self.fields["sub_type_other"].allow_blank = False
                self.fields["sub_type_other"].allow_null = False
            else:
                self.fields.pop("sub_type_other")

            if application_type == CaseTypeSubTypeEnum.F680:
                self.fields["clearance_level"].required = True

            if party_type == PartyType.THIRD_PARTY:
                self.fields["role"].required = True

                if role == PartyRole.OTHER:
                    self.fields["role_other"].required = True
                    self.fields["role_other"].allow_blank = False
                    self.fields["role_other"].allow_null = False
                else:
                    self.fields.pop("role_other")

    def validate(self, data):
        validated_data = super().validate(data)

        if validated_data.get("type") == PartyType.END_USER:
            if "signatory_name_euu" in validated_data and validated_data.get("signatory_name_euu") == "":
                raise serializers.ValidationError({"signatory_name_euu": "Enter a name"})

        return validated_data

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
            value = value.lower()
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

    def get_documents(self, instance):
        docs = PartyDocument.objects.filter(party=instance)
        return PartyDocumentSerializer(docs, many=True).data

    def get_type_display_value(self, instance):
        return instance.get_type_display()


class PartyViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = "__all__"


class PartyDocumentSerializer(serializers.ModelSerializer):
    party = serializers.PrimaryKeyRelatedField(queryset=Party.objects.all())

    class Meta:
        model = PartyDocument
        fields = (
            "id",
            "type",
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
    name = serializers.CharField(error_messages=PartyErrors.NAME, max_length=100)
    email = serializers.EmailField(error_messages=PartyErrors.EMAIL)
    phone_number = serializers.CharField(error_messages=PartyErrors.PHONE_NUMBER, max_length=50)
    details = serializers.CharField(error_messages=PartyErrors.DETAILS, max_length=256)
    address = serializers.CharField(error_messages=PartyErrors.ADDRESS, max_length=256)
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
