from rest_framework import serializers

from cases.models import Notification
from conf.constants import Roles
from conf.exceptions import NotFoundError
from conf.helpers import convert_pascal_case_to_snake_case
from conf.serializers import KeyValueChoiceField
from gov_users.serializers import RoleSerializer
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.models import Organisation
from queries.helpers import get_exporter_query
from queries.models import Query
from teams.serializers import TeamSerializer
from users.enums import UserStatuses
from users.libraries.get_user import get_user_by_pk, get_exporter_user_by_email
from users.models import ExporterUser, BaseUser, GovUser, UserOrganisationRelationship, Role


class BaseUserViewSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        instance = get_user_by_pk(instance.id)

        if isinstance(instance, ExporterUser):
            return ExporterUserViewSerializer(instance=instance).data
        else:
            return GovUserViewSerializer(instance=instance).data

    class Meta:
        model = BaseUser
        fields = "__all__"


class ExporterUserViewSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    organisations = serializers.SerializerMethodField()

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

    class Meta:
        model = ExporterUser
        fields = "__all__"


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
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    organisation = serializers.PrimaryKeyRelatedField(
        queryset=Organisation.objects.all(), required=False, write_only=True
    )

    class Meta:
        model = ExporterUser
        fields = ("id", "email", "first_name", "last_name", "organisation")

    def validate_email(self, email):
        if hasattr(self, "initial_data") and "organisation" in self.initial_data:
            try:
                organisation = get_organisation_by_pk(self.initial_data["organisation"])

                if UserOrganisationRelationship.objects.get(
                    user=get_exporter_user_by_email(self.initial_data["email"]), organisation=organisation,
                ):
                    raise serializers.ValidationError(
                        self.initial_data["email"] + " is already a member of this organisation."
                    )
            except (NotFoundError, UserOrganisationRelationship.DoesNotExist):
                pass

        return email

    def create(self, validated_data):
        organisation = validated_data.pop("organisation")
        exporter, _ = ExporterUser.objects.get_or_create(email=validated_data["email"], defaults={**validated_data})
        if UserOrganisationRelationship.objects.filter(organisation=organisation).count() > 1:
            UserOrganisationRelationship(user=exporter, organisation=organisation).save()
        else:
            UserOrganisationRelationship(user=exporter,
                                         organisation=organisation,
                                         role=Role.objects.get(
                                             id=Roles.EXPORTER_SUPER_USER_ROLE_ID
                                         )).save()
        return exporter

    def update(self, instance, validated_data):
        """
        Update and return an existing `User` instance, given the validated data.
        """
        instance.email = validated_data.get("email", instance.email)
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.save()
        return instance


class ExporterUserCreateSerializer(serializers.ModelSerializer):
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=True)
    email = serializers.EmailField(
        error_messages={"invalid": "Enter an email address in the correct format, like name@example.com"}
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    def create(self, validated_data):
        organisation = validated_data.pop("organisation")
        exporter, _ = ExporterUser.objects.get_or_create(email=validated_data["email"], defaults={**validated_data})
        UserOrganisationRelationship(user=exporter, organisation=organisation).save()
        return exporter

    class Meta:
        model = ExporterUser
        fields = ("id", "email", "first_name", "last_name", "organisation")


class CaseNotificationGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("case_activity",)


class NotificationSerializer(serializers.ModelSerializer):
    object = serializers.SerializerMethodField()
    object_type = serializers.SerializerMethodField()

    parent = serializers.SerializerMethodField()
    parent_type = serializers.SerializerMethodField()

    def get_object(self, obj):
        object = next(
            item
            for item in [getattr(obj, "case_note"), getattr(obj, "query"), getattr(obj, "ecju_query"),]
            if item is not None
        )
        return object.id

    def get_object_type(self, obj):
        object = next(
            item
            for item in [getattr(obj, "case_note"), getattr(obj, "query"), getattr(obj, "ecju_query"),]
            if item is not None
        )

        if isinstance(object, Query):
            object = get_exporter_query(object)

        return convert_pascal_case_to_snake_case(object.__class__.__name__)

    def get_parent(self, obj):
        if obj.case_note:
            object = next(
                item for item in [obj.case_note.case.application, obj.case_note.case.query] if item is not None
            )
        if obj.ecju_query:
            object = next(
                item for item in [obj.ecju_query.case.application, obj.ecju_query.case.query] if item is not None
            )

        if obj.query:
            return None

        return object.id

    def get_parent_type(self, obj):
        if obj.case_note:
            object = next(
                item for item in [obj.case_note.case.application, obj.case_note.case.query] if item is not None
            )
        if obj.ecju_query:
            object = next(
                item for item in [obj.ecju_query.case.application, obj.ecju_query.case.query] if item is not None
            )

        if obj.query:
            return None

        if isinstance(object, Query):
            object = get_exporter_query(object)

        return convert_pascal_case_to_snake_case(object.__class__.__name__)

    class Meta:
        model = Notification
        fields = ("object", "object_type", "parent", "parent_type")


def _get_notification_case(notification):
    if notification.case_note:
        return notification.case_note.case
    elif notification.ecju_query:
        return notification.ecju_query.case
    elif notification.query:
        return notification.query.case
    else:
        raise Exception("Unexpected error, Notification object with no link to originating object")


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

    class Meta:
        model = UserOrganisationRelationship
        fields = ("status",)
