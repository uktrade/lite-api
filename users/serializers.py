from rest_framework import serializers

from organisations.serializers import OrganisationViewSerializer
from users.models import User


class ViewUserSerializer(serializers.ModelSerializer):
    organisation = OrganisationViewSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'organisation')
