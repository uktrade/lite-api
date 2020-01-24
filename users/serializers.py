from rest_framework import serializers

from conf.constants import Roles
from conf.exceptions import NotFoundError
from conf.serializers import KeyValueChoiceField
from gov_users.serializers import RoleSerializer
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.models import Organisation, Site
from teams.serializers import TeamSerializer
from users.enums import UserStatuses, UserType
from users.libraries.get_user import get_user_by_pk, get_exporter_user_by_email, get_user_organisation_relationship
from users.models import (
    ExporterUser,
    BaseUser,
    GovUser,
    UserOrganisationRelationship,
    Role,
    ExporterNotification,
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
    organisations = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    sites = serializers.SerializerMethodField()

    class Meta:
        model = ExporterUser
        fields = "__all__"

    def get_status(self, instance):
        if hasattr(instance, "status"):
            return instance.status

        return None

    def get_organisations(self, instance):
        try:
            user_organisation_relationships = UserOrganisationRelationship.objects.filter(user=instance)
            return_value = []

            for relationship in user_organisation_relationships:
                return_value.append(
                    {
                        "id": relationship.organisation.id,
                        "name": relationship.organisation.name,
                        "joined_at": relationship.created_at,
                    }
                )

            return return_value
        except UserOrganisationRelationship.DoesNotExist:
            raise NotFoundError({"user": "User not found - " + str(instance.id)})

    def get_role(self, instance):
        if self.context:
            role = get_user_organisation_relationship(instance, self.context).role
            return RoleSerializer(role).data
        return None

    def get_sites(self, instance):
        from organisations.serializers import SiteViewSerializer

        if self.context:
            sites = Site.objects.get_by_user_and_organisation(instance, self.context)
            return SiteViewSerializer(sites, many=True).data
        return None


class GovUserViewSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    role = RoleSerializer()

    class Meta:
        model = GovUser
        fields = "__all__"


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
        if hasattr(self, "initial_data") and "role" in self.initial_data:
            try:
                if self.initial_data["role"] not in Roles.EXPORTER_PRESET_ROLES:
                    Role.objects.get(id=self.initial_data["role"], organisation=self.initial_data["organisation"])
            except NotFoundError:
                pass
        return role

    def create(self, validated_data):
        exporter_user = ExporterUser.objects.filter(email__iexact=validated_data["email"])
        organisation = validated_data.pop("organisation", None)
        sites = validated_data.pop("sites", None)
        role = validated_data.pop("role", None)

        if not exporter_user.exists():
            exporter_user = ExporterUser.objects.create(**validated_data)
        else:
            exporter_user = exporter_user.first()

        user_org = UserOrganisationRelationship.objects.filter(user=exporter_user, organisation=organisation)

        if not user_org.exists():
            user_org = UserOrganisationRelationship(
                user=exporter_user,
                organisation=organisation,
                role=Role.objects.get(id=Roles.EXPORTER_SUPER_USER_ROLE_ID),
            )
            user_org.save()
            user_org.sites.set(sites)
        else:
            user_org = user_org.first()
            user_org.role = role or user_org.role
            user_org.save()
            user_org.sites.set(sites)

        return exporter_user

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


class ExporterNotificationSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()
    case = serializers.SerializerMethodField()

    class Meta:
        model = ExporterNotification
        fields = (
            "object_id",
            "content_type",
            "case",
        )

    def get_content_type(self, obj):
        return obj.content_type.model

    def get_case(self, obj):
        return {"id": obj.case.id, "type": obj.case.type}


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
