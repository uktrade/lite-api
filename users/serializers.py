from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer
from users.models import User


class ViewUserSerializer(serializers.ModelSerializer):
    organisation = OrganisationViewSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
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
                  'organisation')


class UserViewSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'organisation')
