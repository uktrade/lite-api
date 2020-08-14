from rest_framework import serializers

from api.conf.constants import Roles
from api.conf.exceptions import NotFoundError
from api.conf.serializers import KeyValueChoiceField
from gov_users.serializers import RoleSerializer, GovUserViewSerializer
from api.organisations.libraries.get_organisation import get_organisation_by_pk
from api.organisations.models import Organisation, Site
from api.users.enums import UserStatuses, UserType
from api.users.libraries.get_user import get_user_by_pk, get_exporter_user_by_email
from api.users.models import (
    ExporterUser,
    BaseUser,
    UserOrganisationRelationship,
    Role,
)


class BaseUserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseUser
        fields = "__all__"

    def to_representation(self, instance):
        instance = get_user_by_pk(instance.id)

        if isinstance(instance, ExporterUser):
            return ExporterUserViewSerializer(instance=instance).data
        else:
            return GovUserViewSerializer(instance=instance).data


class ExporterUserViewSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    sites = serializers.SerializerMethodField()

    class Meta:
        model = ExporterUser
        fields = "__all__"

    def get_status(self, instance):
        if hasattr(instance, "status"):
            return instance.status

        return None

    def get_role(self, _):
        if self.context:
            return RoleSerializer(self.context.role).data

    def get_sites(self, _):
        from api.organisations.serializers import SiteListSerializer

        if self.context:
            sites = Site.objects.get_by_user_organisation_relationship(self.context)
            return SiteListSerializer(sites, many=True).data
        return None


class ExporterUserCreateUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        error_messages={"invalid": "Enter an email address in the correct format, like name@example.com"}
    )
    organisation = serializers.PrimaryKeyRelatedField(
        queryset=Organisation.objects.all(), required=False, write_only=True
    )
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), write_only=True, required=False)
    sites = serializers.PrimaryKeyRelatedField(queryset=Site.objects.all(), write_only=True, many=True)

    class Meta:
        model = ExporterUser
        fields = (
            "id",
            "email",
            "role",
            "organisation",
            "sites",
        )

    def validate_email(self, email):
        if hasattr(self, "initial_data") and "organisation" in self.initial_data:
            try:
                organisation = get_organisation_by_pk(self.initial_data["organisation"])

                if UserOrganisationRelationship.objects.get(
                    user=get_exporter_user_by_email(self.initial_data["email"]), organisation=organisation
                ):
                    raise serializers.ValidationError(
                        self.initial_data["email"] + " is already a member of this organisation."
                    )
            except (NotFoundError, UserOrganisationRelationship.DoesNotExist):
                pass

        return email

    def validate_role(self, role):
        if role:
            if role.pk not in Roles.EXPORTER_PRESET_ROLES:
                try:
                    role = Role.objects.get(
                        id=self.initial_data["role"], organisation_id=self.initial_data["organisation"]
                    )
                except Role.DoesNotExist:
                    role = Role.objects.get(id=Roles.EXPORTER_DEFAULT_ROLE_ID)
        return role

    def clean_email(self, email):
        return email.lower() if email else None

    def create(self, validated_data):
        organisation = validated_data.pop("organisation")
        sites = validated_data.pop("sites")
        role = validated_data.pop("role", Role.objects.get(id=Roles.EXPORTER_DEFAULT_ROLE_ID))

        exporter, _ = ExporterUser.objects.get_or_create(email__iexact=validated_data["email"], defaults=validated_data)

        if UserOrganisationRelationship.objects.filter(organisation=organisation).exists():
            relationship = UserOrganisationRelationship(user=exporter, organisation=organisation, role=role)
            relationship.save()
            relationship.sites.set(sites)
        else:
            relationship = UserOrganisationRelationship(
                user=exporter, organisation=organisation, role=Role.objects.get(id=Roles.EXPORTER_SUPER_USER_ROLE_ID)
            )
            relationship.save()
            relationship.sites.set(sites)

        return exporter

    def update(self, instance, validated_data):
        """
        Update and return an existing `User` instance, given the validated data.
        """
        email = validated_data.get("email")
        if email:
            exporter_user = ExporterUser.objects.filter(email__iexact=email)
            if not exporter_user.exists():
                instance.email = email
                instance.save()
        return instance


class ExporterUserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExporterUser
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
        )


class UserOrganisationRelationshipSerializer(serializers.ModelSerializer):
    status = KeyValueChoiceField(choices=UserStatuses.choices)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.filter(type=UserType.EXPORTER))

    class Meta:
        model = UserOrganisationRelationship
        fields = (
            "status",
            "role",
        )
