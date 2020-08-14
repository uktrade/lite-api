import re

from django.db import transaction
from rest_framework import serializers

from addresses.models import Address
from addresses.serializers import AddressSerializer
from api.conf.constants import ExporterPermissions
from api.conf.helpers import str_to_bool
from api.conf.serializers import (
    PrimaryKeyRelatedSerializerField,
    KeyValueChoiceField,
    CountrySerializerField,
)
from lite_content.lite_api import strings
from lite_content.lite_api.strings import Organisations
from api.organisations.constants import UK_VAT_VALIDATION_REGEX
from api.organisations.enums import OrganisationType, OrganisationStatus, LocationType
from api.organisations.models import Organisation, Site, ExternalLocation
from static.countries.helpers import get_country
from users.libraries.get_user import get_user_organisation_relationship
from users.models import GovUser, UserOrganisationRelationship, ExporterUser
from users.serializers import ExporterUserCreateUpdateSerializer, ExporterUserSimpleSerializer


class SiteListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    address = AddressSerializer()
    records_located_at = serializers.SerializerMethodField()

    def get_records_located_at(self, instance):
        if instance.site_records_located_at:
            site = instance.site_records_located_at
            return {
                "id": site.id,
                "name": site.name,
                "address": {
                    "address_line_1": site.address.address_line_1,
                    "address_line_2": site.address.address_line_2,
                    "region": site.address.region,
                    "postcode": site.address.postcode,
                    "city": site.address.city,
                    "country": {"name": site.address.country.name},
                },
            }


class SiteViewSerializer(SiteListSerializer):
    users = serializers.SerializerMethodField()
    admin_users = serializers.SerializerMethodField()
    is_used_on_application = serializers.BooleanField(required=False)

    def get_users(self, instance):
        users = (
            UserOrganisationRelationship.objects.filter(sites__id=instance.id)
            .select_related("user")
            .order_by("user__email")
        )
        return ExporterUserSimpleSerializer([x.user for x in users], many=True).data

    def get_admin_users(self, instance):
        users = (
            UserOrganisationRelationship.objects.filter(
                organisation=instance.organisation, role__permissions__id=ExporterPermissions.ADMINISTER_SITES.name
            )
            .select_related("user")
            .order_by("user__email")
        )
        return ExporterUserSimpleSerializer([x.user for x in users], many=True).data

    class Meta:
        model = Site
        fields = (
            "id",
            "name",
            "address",
            "records_located_at",
            "users",
            "admin_users",
            "is_used_on_application",
        )


class SiteCreateUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages={"blank": "Enter a name for your site"}, write_only=True)
    address = AddressSerializer()
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)
    users = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all(), many=True, required=False)
    site_records_located_at = serializers.PrimaryKeyRelatedField(queryset=Site.objects.all(), required=False)

    class Meta:
        model = Site
        fields = ("id", "name", "address", "organisation", "users", "site_records_located_at")

    @transaction.atomic
    def create(self, validated_data):
        users = []
        if "users" in validated_data:
            users = validated_data.pop("users")

        address_data = validated_data.pop("address")
        address_data["country"] = address_data["country"].id

        address_serializer = AddressSerializer(data=address_data)
        if address_serializer.is_valid(raise_exception=True):
            address = Address(**address_serializer.validated_data)
            address.save()

        site = Site.objects.create(address=address, **validated_data)

        if users:
            site.users.set([get_user_organisation_relationship(user, validated_data["organisation"]) for user in users])

        if "site_records_stored_here" in self.initial_data:
            if str_to_bool(self.initial_data.get("site_records_stored_here")):
                site.site_records_located_at = site
                site.save()

        return site

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.site_records_located_at = validated_data.get(
            "site_records_located_at", instance.site_records_located_at
        )
        instance.save()
        return instance


class OrganisationCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(error_messages={"blank": Organisations.Create.BLANK_NAME})
    type = KeyValueChoiceField(choices=OrganisationType.choices)
    eori_number = serializers.CharField(
        max_length=17,
        required=False,
        allow_null=True,
        allow_blank=True,
        error_messages={"blank": Organisations.Create.BLANK_EORI, "max_length": Organisations.Create.LENGTH_EORI},
    )
    vat_number = serializers.CharField(
        min_length=7,
        max_length=17,
        required=False,
        allow_null=True,
        allow_blank=True,
        error_messages={
            "blank": Organisations.Create.BLANK_VAT,
            "min_length": Organisations.Create.LENGTH_VAT,
            "max_length": Organisations.Create.LENGTH_VAT,
        },
    )
    sic_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        min_length=4,
        max_length=5,
        error_messages={
            "blank": Organisations.Create.BLANK_SIC,
            "min_length": Organisations.Create.LENGTH_SIC,
            "max_length": Organisations.Create.LENGTH_SIC,
        },
    )
    registration_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        min_length=8,
        max_length=8,
        error_messages={
            "blank": Organisations.Create.BLANK_REGISTRATION_NUMBER,
            "min_length": Organisations.Create.LENGTH_REGISTRATION_NUMBER,
            "max_length": Organisations.Create.LENGTH_REGISTRATION_NUMBER,
        },
    )
    user = ExporterUserCreateUpdateSerializer(write_only=True)
    site = SiteCreateUpdateSerializer(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        organisation_type = self.initial_data.get("type") or self.instance.type
        in_uk = self.initial_data.get("location", "united_kingdom") == "united_kingdom"

        if self.instance:
            in_uk = self.instance.primary_site.address.country == get_country("GB")

        if organisation_type != OrganisationType.HMRC and in_uk:
            self.fields["eori_number"].allow_blank = False
            self.fields["eori_number"].allow_null = False

        if organisation_type == OrganisationType.COMMERCIAL and in_uk:
            self.fields["vat_number"].allow_blank = False
            self.fields["vat_number"].allow_null = False
            self.fields["registration_number"].allow_blank = False
            self.fields["registration_number"].allow_null = False
            self.fields["sic_number"].allow_blank = False
            self.fields["sic_number"].allow_null = False

        if "data" in kwargs:
            if "user" in kwargs["data"]:
                kwargs["data"]["user"]["sites"] = kwargs["data"]["user"].get("sites", [])

    class Meta:
        model = Organisation
        fields = (
            "id",
            "name",
            "type",
            "status",
            "eori_number",
            "sic_number",
            "vat_number",
            "registration_number",
            "user",
            "site",
        )

    def validate_sic_number(self, value):
        if value:
            if not value.isdigit():
                raise serializers.ValidationError(Organisations.Create.ONLY_ENTER_NUMBERS)

            int_value = int(value)
            if int_value < 1110 or int_value > 99999:
                raise serializers.ValidationError(Organisations.Create.INVALID_SIC)
        return value

    def validate_vat_number(self, value):
        if value:
            stripped_vat = re.sub(r"[^A-Z0-9]", "", value)
            if not re.match(r"%s" % UK_VAT_VALIDATION_REGEX, stripped_vat):
                raise serializers.ValidationError(Organisations.Create.INVALID_VAT)
            return stripped_vat
        return value

    @transaction.atomic
    def create(self, validated_data):
        if self.context["validate_only"]:
            return

        user_data = validated_data.pop("user")
        site_data = validated_data.pop("site")
        organisation = Organisation.objects.create(**validated_data)
        user_data["organisation"] = organisation.id

        site_data["address"]["country"] = site_data["address"]["country"].id

        site_serializer = SiteCreateUpdateSerializer(data=site_data)
        if site_serializer.is_valid(raise_exception=True):
            site = site_serializer.save()
            # Set the site records are located at to the site itself
            site.site_records_located_at = site
            site.save()
        user_serializer = ExporterUserCreateUpdateSerializer(data={"sites": [site.id], **user_data})
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()

        organisation.primary_site = site
        organisation.save()

        organisation.primary_site.organisation = organisation
        organisation.primary_site.save()

        return organisation


class OrganisationStatusUpdateSerializer(serializers.ModelSerializer):
    status = KeyValueChoiceField(choices=OrganisationStatus.choices, required=True, allow_null=False, allow_blank=False)

    class Meta:
        model = Organisation
        fields = ("status",)


class TinyOrganisationViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("id", "name")


class OrganisationListSerializer(serializers.ModelSerializer):
    type = KeyValueChoiceField(OrganisationType.choices)
    status = KeyValueChoiceField(OrganisationStatus.choices)

    class Meta:
        model = Organisation
        fields = (
            "id",
            "name",
            "sic_number",
            "eori_number",
            "type",
            "status",
            "registration_number",
            "vat_number",
            "created_at",
        )


class OrganisationDetailSerializer(serializers.ModelSerializer):
    primary_site = PrimaryKeyRelatedSerializerField(queryset=Site.objects.all(), serializer=SiteListSerializer)
    type = KeyValueChoiceField(OrganisationType.choices)
    flags = serializers.SerializerMethodField()
    status = KeyValueChoiceField(OrganisationStatus.choices)

    def get_flags(self, instance):
        # TODO remove try block when other end points adopt generics
        try:
            if isinstance(self.context.get("request").user, GovUser):
                return list(instance.flags.values("id", "name", "colour", "label", "priority"))
        except AttributeError:
            return list(instance.flags.values("id", "name", "colour", "label", "priority"))

    class Meta:
        model = Organisation
        fields = "__all__"


class OrganisationCaseSerializer(serializers.Serializer):
    name = serializers.CharField()
    primary_site = SiteListSerializer()


class ExternalLocationSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = CountrySerializerField(required=True)
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = ExternalLocation
        fields = ("id", "name", "address", "country", "organisation")


class SiclExternalLocationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages={"blank": strings.ExternalLocations.Errors.NULL_NAME})
    address = serializers.CharField(error_messages={"blank": strings.ExternalLocations.Errors.NULL_ADDRESS})
    country = CountrySerializerField(required=False)
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    location_type = serializers.CharField(
        required=True,
        error_messages={
            "required": strings.ExternalLocations.Errors.LOCATION_TYPE,
            "blank": strings.ExternalLocations.Errors.LOCATION_TYPE,
        },
    )

    def validate(self, data):
        if data["location_type"] == LocationType.LAND_BASED and not data["country"]:
            raise serializers.ValidationError({"country": strings.Addresses.NULL_COUNTRY})
        return super().validate(data)

    class Meta:
        model = ExternalLocation
        fields = ("id", "name", "address", "country", "organisation", "location_type")


class OrganisationUserListView(serializers.ModelSerializer):
    role_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = ExporterUser
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "role_name",
            "status",
        )
