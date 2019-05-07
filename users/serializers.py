from django.contrib.auth.hashers import make_password
from enumchoicefield import EnumChoiceField
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from organisations.models import Organisation
from users.models import User, UserStatuses


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
        Update and return an existing `User` instance, given the validated data.
        """
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.status = validated_data.get('status', instance.status)
        if validated_data.get('password') is not None:
            instance.password = make_password(validated_data.get('password'))
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        error_messages={'invalid': 'Enter an email address in the correct format, like name@example.com'})
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True)
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password', 'organisation')

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return User.objects.create(**validated_data)
