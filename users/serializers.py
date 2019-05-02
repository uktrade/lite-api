from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer
from users.models import User


class ViewUserSerializer(serializers.ModelSerializer):
    organisation = OrganisationViewSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'organisation')


class UserBaseSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(
        error_messages={'invalid': 'Enter an email address in the correct format, like name@example.com'})
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'organisation')