from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from users.models import User


class UserViewSerializer(serializers.ModelSerializer):
    # organisation = OrganisationViewSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'organisation')


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        error_messages={'invalid': 'Enter an email address in the correct format, like name@example.com'})
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return User.objects.create(**validated_data)
