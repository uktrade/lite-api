from rest_framework import serializers

from users.models import User


class ViewUserSerializer(serializers.ModelSerializer):
    # organisation = OrganisationViewSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'organisation')


class UserBaseSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        error_messages={'invalid': 'Enter an email address in the correct format, like name@example.com'})
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')
