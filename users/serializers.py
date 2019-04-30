from django.contrib.auth.hashers import make_password
from enumchoicefield import EnumChoiceField
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer
from users.models import User, UserStatuses


class ViewUserSerializer(serializers.ModelSerializer):
    organisation = OrganisationViewSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'status',
                  'organisation')


class UserSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'password',
                  'status',
                  'organisation')

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return super(UserSerializer, self).create(validated_data)


class UserViewSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'status',
                  'organisation')


class UserUpdateSerializer(UserSerializer):
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    status = EnumChoiceField(enum_class=UserStatuses)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.status = validated_data.get('status', instance.status)
        instance.password = make_password(validated_data.get('password'))
        instance.save()
        return instance