from django.db import transaction
from rest_framework import serializers

from addresses.models import Address, ForeignAddress
from addresses.serializers import AddressSerializer, ForeignAddressSerializer
from conf.constants import ExporterPermissions
from conf.serializers import (
    PrimaryKeyRelatedSerializerField,
    KeyValueChoiceField,
    CountrySerializerField,
)
from lite_content.lite_api.strings import Organisations
from organisations.enums import OrganisationType, OrganisationStatus
from organisations.models import Organisation, Site, ExternalLocation
from users.libraries.get_user import get_user_organisation_relationship
from users.models import GovUser, UserOrganisationRelationship, Permission, ExporterUser
from users.serializers import ExporterUserCreateUpdateSerializer, ExporterUserSimpleSerializer


class SiteListSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    foreign_address = ForeignAddressSerializer()

    def to_representation(self, value):
        repr_dict = super(SiteListSerializer, self).to_representation(value)
        if not repr_dict["address"]:
            del repr_dict["address"]
        if not repr_dict["foreign_address"]:
            del repr_dict["foreign_address"]
        return repr_dict

    class Meta:
        model = Site
        fields = ("id", "name", "address", "foreign_address")


class SiteViewSerializer(SiteListSerializer):
    users = serializers.SerializerMethodField()

    def get_users(self, instance):
        users = set([x.user for x in UserOrganisationRelationship.objects.filter(sites__id__exact=instance.id)])
        permission = Permission.objects.get(id=ExporterPermissions.ADMINISTER_SITES.name)
        users_with_permission = set(
            [
                x.user
                for x in UserOrganisationRelationship.objects.filter(
                    organisation=instance.organisation, role__permissions__id=permission.id
                )
            ]
        )
        users_union = users.union(users_with_permission)
        users_union = sorted(users_union, key=lambda x: x.first_name)
        return ExporterUserSimpleSerializer(users_union, many=True).data

    class Meta:
        model = Site
        fields = ("id", "name", "address", "foreign_address", "users")


class SiteCreateUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages={"blank": "Enter a name for your site"}, write_only=True)
    address = AddressSerializer(write_only=True, required=False)
    foreign_address = ForeignAddressSerializer(write_only=True, required=False)
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)
    users = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all(), many=True, required=False)

    class Meta:
        model = Site
        fields = ("id", "name", "address", "foreign_address", "organisation", "users")

    def validate(self, data):
        validated_data = super().validate(data)

        # For creating you have to have provide an address or foreign address
        if not self.partial:
            if "address" not in validated_data and "foreign_address" not in validated_data:
                raise serializers.ValidationError({"address": "You have to have an address!"})

        # Sites have to have either address or foreign address
        if "address" in validated_data and "foreign_address" in validated_data:
            raise serializers.ValidationError({"address": "You cant have both!"})

        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        users = []
        if "users" in validated_data:
            users = validated_data.pop("users")

        if "address" in validated_data:
            address_data = validated_data.pop("address")
            address_data["country"] = address_data["country"].id

            address_serializer = AddressSerializer(data=address_data)
            if address_serializer.is_valid(raise_exception=True):
                address = Address(**address_serializer.validated_data)
                address.save()

            site = Site.objects.create(address=address, **validated_data)
        else:
            foreign_address_data = validated_data.pop("foreign_address")
            foreign_address_data["country"] = foreign_address_data["country"].id

            foreign_address_serializer = ForeignAddressSerializer(data=foreign_address_data)
            if foreign_address_serializer.is_valid(raise_exception=True):
                foreign_address = ForeignAddress(**foreign_address_serializer.validated_data)
                foreign_address.save()

            site = Site.objects.create(foreign_address=foreign_address, **validated_data)

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
        allow_blank=True,
        error_messages={"blank": Organisations.Create.BLANK_EORI, "max_length": Organisations.Create.LENGTH_EORI},
    )
    vat_number = serializers.CharField(
        min_length=9,
        max_length=9,
        required=False,
        allow_blank=True,
        error_messages={
            "blank": Organisations.Create.BLANK_VAT,
            "min_length": Organisations.Create.LENGTH_VAT,
            "max_length": Organisations.Create.LENGTH_VAT,
        },
    )
    sic_number = serializers.CharField(
        required=False,
        min_length=5,
        max_length=5,
        error_messages={
            "blank": Organisations.Create.BLANK_SIC,
            "min_length": Organisations.Create.LENGTH_SIC,
            "max_length": Organisations.Create.LENGTH_SIC,
        },
    )
    registration_number = serializers.CharField(
        required=False,
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
        if "data" in kwargs:
            if "user" in kwargs["data"]:
                kwargs["data"]["user"]["sites"] = kwargs["data"]["user"].get("sites", [])
        super().__init__(*args, **kwargs)

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

    def validate_eori_number(self, value):
        if self.initial_data.get("type") != OrganisationType.HMRC and not value:
            raise serializers.ValidationError(Organisations.Create.BLANK_EORI)
        return value

    def validate_sic_number(self, value):
        if value:
            if not value.isdigit():
                raise serializers.ValidationError(Organisations.Create.ONLY_ENTER_NUMBERS)

            int_value = int(value)
            if int_value < 1110 or int_value > 99999:
                raise serializers.ValidationError(Organisations.Create.INVALID_SIC)

        if self.initial_data.get("type") == OrganisationType.COMMERCIAL and not value:
            raise serializers.ValidationError(Organisations.Create.BLANK_SIC)
        return value

    def validate_vat_number(self, value):
        if value:
            if not value.startswith("GB"):
                raise serializers.ValidationError(Organisations.Create.INVALID_VAT)

        if self.initial_data.get("type") == OrganisationType.COMMERCIAL and not value:
            raise serializers.ValidationError(Organisations.Create.BLANK_VAT)
        return value

    def validate_registration_number(self, value):
        if self.initial_data.get("type") == OrganisationType.COMMERCIAL and not value:
            raise serializers.ValidationError(Organisations.Create.BLANK_REGISTRATION_NUMBER)
        return value

    @transaction.atomic
    def create(self, validated_data):
        if self.context["validate_only"]:
            return

        user_data = validated_data.pop("user")
        site_data = validated_data.pop("site")
        organisation = Organisation.objects.create(**validated_data)
        user_data["organisation"] = organisation.id

        if "address" in site_data:
            site_data["address"]["country"] = site_data["address"]["country"].id
        else:
            site_data["foreign_address"]["country"] = site_data["foreign_address"]["country"].id

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
                return list(instance.flags.values("id", "name"))
        except AttributeError:
            return list(instance.flags.values("id", "name"))

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
