from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from addresses.models import Address
from addresses.serializers import AddressSerializer
from conf.constants import ExporterPermissions
from conf.serializers import (
    PrimaryKeyRelatedSerializerField,
    KeyValueChoiceField,
    CountrySerializerField,
)
from lite_content.lite_api.strings import Organisations
from organisations.enums import OrganisationType, OrganisationStatus
from organisations.models import Organisation, Site, ExternalLocation
from static.countries.helpers import get_country
from users.libraries.get_user import get_user_organisation_relationship
from users.models import GovUser, UserOrganisationRelationship, ExporterUser
from users.serializers import ExporterUserCreateUpdateSerializer, ExporterUserSimpleSerializer


class SiteListSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    assigned_users_count = serializers.SerializerMethodField()

    def get_assigned_users_count(self, instance):
        return (
            UserOrganisationRelationship.objects.filter(
                Q(sites__id__exact=instance.id)
                | Q(organisation=instance.organisation, role__permissions__id=ExporterPermissions.ADMINISTER_SITES.name)
            )
            .distinct()
            .count()
        )

    class Meta:
        model = Site
        fields = ("id", "name", "address", "assigned_users_count")


class SiteViewSerializer(SiteListSerializer):
    users = serializers.SerializerMethodField()
    admin_users = serializers.SerializerMethodField()

    def get_users(self, instance):
        users = (
            UserOrganisationRelationship.objects.filter(sites__id=instance.id)
            .distinct()
            .select_related("user")
            .order_by("user__email")
        )
        return ExporterUserSimpleSerializer([x.user for x in users], many=True).data

    def get_admin_users(self, instance):
        users = (
            UserOrganisationRelationship.objects.filter(
                organisation=instance.organisation, role__permissions__id=ExporterPermissions.ADMINISTER_SITES.name
            )
            .distinct()
            .select_related("user")
            .order_by("user__email")
        )
        return ExporterUserSimpleSerializer([x.user for x in users], many=True).data

    class Meta:
        model = Site
        fields = ("id", "name", "address", "users", "admin_users")


class SiteCreateUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages={"blank": "Enter a name for your site"}, write_only=True)
    address = AddressSerializer()
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)
    users = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all(), many=True, required=False)

    class Meta:
        model = Site
        fields = ("id", "name", "address", "organisation", "users")

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

        return site

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
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
        min_length=9,
        max_length=9,
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
            if not value.startswith("GB"):
                raise serializers.ValidationError(Organisations.Create.INVALID_VAT)
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

        user_serializer = ExporterUserCreateUpdateSerializer(data={"sites": [site.id], **user_data})
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()

        organisation.primary_site = site
        organisation.save()

        organisation.primary_site.organisation = organisation
        organisation.primary_site.save()

        return organisation


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


class ExternalLocationSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = CountrySerializerField()
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = ExternalLocation
        fields = ("id", "name", "address", "country", "organisation")


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
