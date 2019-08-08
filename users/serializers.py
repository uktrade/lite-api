from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.validators import UniqueValidator

from cases.models import Notification
from gov_users.serializers import RoleSerializer
from organisations.models import Organisation
from teams.serializers import TeamSerializer
from users.libraries.get_user import get_user_by_pk
from users.models import ExporterUser, UserStatuses, BaseUser, GovUser


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


class ExporterUserUpdateSerializer(serializers.ModelSerializer):
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


class ExporterUserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=ExporterUser.objects.all())],
        error_messages={
            'invalid': 'Enter an email address in the correct format, like name@example.com'}
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)

    class Meta:
        model = ExporterUser
        fields = ('id', 'email', 'first_name', 'last_name', 'organisation')

    def create(self, validated_data):
        return ExporterUser.objects.create(**validated_data)


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
