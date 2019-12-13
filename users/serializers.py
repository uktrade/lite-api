from rest_framework import serializers

from applications.models import BaseApplication
from cases.enums import CaseTypeEnum
from cases.models import Notification
from conf.constants import Roles
from conf.exceptions import NotFoundError
from conf.helpers import convert_pascal_case_to_snake_case
from conf.serializers import KeyValueChoiceField
from gov_users.serializers import RoleSerializer
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.models import Organisation, Site
from queries.helpers import get_exporter_query
from queries.models import Query
from teams.serializers import TeamSerializer
from users.enums import UserStatuses, UserType
from users.libraries.get_user import get_user_by_pk, get_exporter_user_by_email, get_user_organisation_relationship
from users.models import ExporterUser, BaseUser, GovUser, UserOrganisationRelationship, Role


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
                        "joined_at": relationship.created,
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
            sites = get_user_organisation_relationship(instance, self.context).get_sites().all()
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
        fields = ("id", "email", "role", "organisation", "sites")

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
        organisation = validated_data.pop("organisation")
        sites = validated_data.pop("sites")
        role = Role.objects.get(id=Roles.EXPORTER_DEFAULT_ROLE_ID)
        if "role" in validated_data:
            role = validated_data.pop("role")
        exporter, _ = ExporterUser.objects.get_or_create(email=validated_data["email"], defaults={**validated_data})

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
        instance.email = validated_data.get("email", instance.email)
        instance.save()
        return instance


class CaseNotificationGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("case_activity",)


class NotificationSerializer(serializers.ModelSerializer):
    object = serializers.SerializerMethodField()
    object_type = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    parent_type = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "object",
            "object_type",
            "parent",
            "parent_type",
        )

    def get_object(self, obj):
        return obj.get_item().id

    def get_object_type(self, obj):
        object_item = obj.get_item()

        if isinstance(object_item, Query):
            object_item = get_exporter_query(object_item)

        return convert_pascal_case_to_snake_case(object_item.__class__.__name__)

    def get_parent(self, obj):
        if obj.query:
            return None

        parent = obj.get_case()
        return parent.id if parent else None

    def get_parent_type(self, obj):
        if obj.query:
            return None

        parent = obj.get_case()
        if not parent:
            return None

        if parent.type in [CaseTypeEnum.CLC_QUERY, CaseTypeEnum.END_USER_ADVISORY_QUERY]:
            parent = get_exporter_query(parent)
        elif parent.type in [CaseTypeEnum.APPLICATION, CaseTypeEnum.HMRC_QUERY]:
            parent = BaseApplication.objects.get(pk=parent.id)

        return convert_pascal_case_to_snake_case(parent.__class__.__name__)


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
