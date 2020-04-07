from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from conf.constants import Roles
from conf.exceptions import NotFoundError
from conf.serializers import KeyValueChoiceField
from gov_users.serializers import RoleSerializer
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.models import Organisation, Site
from teams.serializers import TeamSerializer
from users.enums import UserStatuses, UserType
from users.libraries.get_user import get_user_by_pk, get_exporter_user_by_email
from users.models import (
    ExporterUser,
    BaseUser,
    GovUser,
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
        from organisations.serializers import SiteListSerializer

        if self.context:
            sites = Site.objects.get_by_user_organisation_relationship(self.context)
            return SiteListSerializer(sites, many=True).data
        return None


class GovUserViewSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    role = RoleSerializer()

    class Meta:
        model = GovUser
        fields = "__all__"


class ExporterUserCreateUpdateSerializer(serializers.ModelSerializer):
    organisation = serializers.PrimaryKeyRelatedField(
        queryset=Organisation.objects.all(), required=False, write_only=True
    )
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), write_only=True, required=False)
    sites = serializers.PrimaryKeyRelatedField(queryset=Site.objects.all(), write_only=True, many=True)

    class Meta:
        model = ExporterUser
        fields = (
            "email",
            "role",
            "organisation",
            "sites",
        )

    def create(self, validated_data):
        organisation = validated_data.pop("organisation")
        sites = validated_data.pop("sites")
        role = validated_data.pop("role", Role.objects.get(id=Roles.EXPORTER_DEFAULT_ROLE_ID))

        exporter, _ = ExporterUser.objects.get_or_create(email__iexact=validated_data["email"], defaults=validated_data)

        if not UserOrganisationRelationship.objects.filter(organisation=organisation).exists():
            role = Role.objects.get(id=Roles.EXPORTER_SUPER_USER_ROLE_ID)

        relationship, _ = UserOrganisationRelationship.objects.update_or_create(user=exporter, organisation=organisation, role=role)
        relationship.sites.set(sites)

        return exporter

    def update(self, instance, validated_data):
        """
        Update and return an existing `User` instance, given the validated data.
        """
        email = validated_data.get("email")
        if email and not ExporterUser.objects.filter(email__iexact=email).exists():
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
