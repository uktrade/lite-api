from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from cases.models import Notification
from gov_users.serializers import RoleSerializer
from organisations.models import Organisation
from teams.serializers import TeamSerializer
from users.libraries.get_user import get_user_by_pk
from users.models import ExporterUser, UserStatuses, BaseUser, GovUser, UserOrganisationRelationship


class BaseUserViewSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        instance = get_user_by_pk(instance.id)

        if isinstance(instance, ExporterUser):
            return ExporterUserViewSerializer(instance=instance).data
        else:
            return GovUserViewSerializer(instance=instance).data

    class Meta:
        model = BaseUser
        fields = '__all__'


class ExporterUserViewSerializer(serializers.ModelSerializer):
    organisation = serializers.SerializerMethodField()

    def get_organisation(self, instance):
        return {
            'id': instance.organisation.id,
            'name': instance.organisation.name
        }

    class Meta:
        model = ExporterUser
        fields = '__all__'


class GovUserViewSerializer(serializers.ModelSerializer):
    team = TeamSerializer()
    role = RoleSerializer()

    class Meta:
        model = GovUser
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = ExporterUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'status',
                  'organisation')


class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExporterUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'status',
                  'organisation')


class UserUpdateSerializer(UserSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=ExporterUser.objects.all())],
        error_messages={
            'invalid': 'Enter an email address in the correct format, like name@example.com'}
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    status = serializers.ChoiceField(choices=UserStatuses.choices)

    def update(self, instance, validated_data):
        """
        Update and return an existing `User` instance, given the validated data.
        """
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)
    email = serializers.EmailField(
        error_messages={
            'invalid': 'Enter an email address in the correct format, like name@example.com'}
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    def get_a_user_by_email(self, email):
        try:
            return ExporterUser.objects.get(email=email)
        except ExporterUser.DoesNotExist:
            return None

    def user_has_organisation(self, user, organisation_id):
        return UserOrganisationRelationship.objects.filter(user=user, organisation_id=organisation_id).exists()

    def create(self, validated_data):
        exporter_user = self.get_a_user_by_email(self.data['email'])
        if not exporter_user:
            exporter_user = ExporterUser.objects.create(**validated_data)

        if not self.user_has_organisation(exporter_user, validated_data['organisation'].id):
            email = validated_data.pop('email')
            validated_data['organisation'] = validated_data['organisation'].id
            validated_data['user'] = exporter_user
            serializer = UserOrganisationSerializer(data=validated_data)
            if serializer.is_valid(raise_exception=False):
                serializer.save()
                return exporter_user
            return serializer.errors
        return exporter_user

    class Meta:
        model = ExporterUser
        unique_together = ('email', 'organisation')
        fields = ('id', 'email', 'first_name', 'last_name', 'organisation')


class NotificationsSerializer(serializers.ModelSerializer):
    application = serializers.SerializerMethodField()

    def get_application(self, obj):
        case = obj.note.case
        application = case.application
        return application.id

    class Meta:
        model = Notification
        exclude = []


class ClcNotificationsSerializer(serializers.ModelSerializer):
    clc_query = serializers.SerializerMethodField()

    def get_clc_query(self, obj):
        case = obj.note.case
        clc_query = case.clc_query
        return clc_query.id

    class Meta:
        model = Notification
        exclude = []


class UserOrganisationSerializer(serializers.ModelSerializer):
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all())

    class Meta:
        model = UserOrganisationRelationship
        exclude = []
