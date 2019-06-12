from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from gov_users.models import GovUser
from teams.models import Team


class GovUserSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())

    class Meta:
        model = GovUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'status',
                  'team')